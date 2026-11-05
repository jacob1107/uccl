#!/usr/bin/env python3
"""
Local unit-test for UCCL P2P Engine — server writes data with RDMA-WRITE
using the new one-sided metadata handshake.

Covers all four src/dst memory combinations (gpu->gpu, gpu->cpu, cpu->gpu,
cpu->cpu). Host-memory combinations regression-test the NCCL transport's
device-staging path: NCCL p2p kernels can only dereference GPU-visible
memory, so host buffers must be staged through a device buffer or the
matched ops wedge both endpoints.
"""

from __future__ import annotations
import sys, time, multiprocessing
from typing import Tuple

# You must first import torch before importing uccl for AMD GPUs
import torch

try:
    from uccl import p2p
except ImportError as e:
    sys.stderr.write(f"Failed to import p2p: {e}\n")
    raise


WRITE_VALUE = 7.0
# Larger than one 2 MiB staging chunk so host-buffer transfers exercise the
# chunked staging loop, not just the single-chunk fast path.
BIG_NBYTES = 5 * 1024 * 1024
SMALL_NBYTES = 4 * 1024


def parse_endpoint_meta(meta: bytes) -> Tuple[str, int, str]:
    """Return (ip, port, remote_gpu_bdf)."""
    return p2p.Endpoint.parse_metadata(meta)


def _make_buffer(nbytes: int, device: str) -> torch.Tensor:
    n = nbytes // 4
    if device == "gpu":
        return torch.zeros(n, dtype=torch.float32, device="cuda:0")
    # Intentionally pageable host memory: the worst case for GPU access.
    return torch.zeros(n, dtype=torch.float32)


def _sync(tensor: torch.Tensor) -> None:
    if tensor.device.type == "cuda":
        torch.cuda.synchronize()


def _wait_for_value(tensor: torch.Tensor, value: float, timeout_s: float = 60.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        _sync(tensor)
        if bool((tensor == value).all()):
            return True
        time.sleep(0.05)
    return False


def test_local(src_device: str = "gpu", dst_device: str = "gpu",
               nbytes: int = SMALL_NBYTES):
    print(f"Running RDMA-WRITE local test ({src_device} -> {dst_device}, "
          f"{nbytes} bytes)")
    meta_parent, meta_child = multiprocessing.Pipe()
    fifo_parent, fifo_child = multiprocessing.Pipe()

    def server_proc(ep_meta_q, fifo_meta_q):
        ep_meta = ep_meta_q.recv()
        ip, port, r_gpu = parse_endpoint_meta(ep_meta)

        ep = p2p.Endpoint(local_gpu_idx=0)
        ok, conn_id = ep.connect(ip, r_gpu, remote_port=port)
        assert ok, "connect failed"
        print(f"[Server] connected (conn_id={conn_id})")

        tensor = torch.full((nbytes // 4,), WRITE_VALUE, dtype=torch.float32,
                            device="cuda:0" if src_device == "gpu" else "cpu")
        _sync(tensor)
        ok, mr_id = ep.reg(tensor.data_ptr(), nbytes)
        assert ok

        fifo_meta = fifo_meta_q.recv()
        assert isinstance(fifo_meta, (bytes, bytearray)) and len(fifo_meta) == 64

        ok = ep.write(conn_id, mr_id, tensor.data_ptr(), nbytes, fifo_meta)
        assert ok, "write failed"

        _sync(tensor)
        print("✓ Server write completed")

    def client_proc(ep_meta_q, fifo_meta_q):
        ep = p2p.Endpoint(local_gpu_idx=0)
        ep_meta_q.send(bytes(ep.get_metadata()))

        ok, r_ip, r_gpu, conn_id = ep.accept()
        assert ok, "accept failed"
        print(f"[Client] accepted (conn_id={conn_id})")

        tensor = _make_buffer(nbytes, dst_device)
        _sync(tensor)

        ok, mr_id = ep.reg(tensor.data_ptr(), nbytes)
        assert ok
        ok, fifo_blob = ep.advertise(mr_id, tensor.data_ptr(), nbytes)
        assert isinstance(fifo_blob, (bytes, bytearray)) and len(fifo_blob) == 64
        print(f"Buffer exposed for RDMA WRITE ({dst_device})")

        fifo_meta_q.send(bytes(fifo_blob))
        assert _wait_for_value(tensor, WRITE_VALUE), \
            f"receiver buffer never got {WRITE_VALUE}; " \
            f"first elements: {tensor[:4].tolist()}"
        print("✓ Client received written data")

    srv = multiprocessing.Process(target=server_proc, args=(meta_parent, fifo_parent))
    cli = multiprocessing.Process(target=client_proc, args=(meta_child, fifo_child))
    srv.start()
    time.sleep(1)
    cli.start()
    # A wedged transfer (e.g. host buffers handed to NCCL unstaged) hangs
    # forever; bound the wait and kill instead of blocking the suite.
    srv.join(120)
    cli.join(120)
    if srv.is_alive() or cli.is_alive():
        srv.terminate()
        cli.terminate()
        srv.join()
        cli.join()
        raise AssertionError(
            f"write {src_device}->{dst_device} hung; transfer never completed")
    assert srv.exitcode == 0, f"server failed ({src_device} src): exit {srv.exitcode}"
    assert cli.exitcode == 0, f"client failed ({dst_device} dst): exit {cli.exitcode}"
    print(f"Local RDMA-WRITE test passed ({src_device} -> {dst_device})\n")


if __name__ == "__main__":
    try:
        for src_dev, dst_dev in [("gpu", "gpu"), ("gpu", "cpu"),
                                 ("cpu", "gpu"), ("cpu", "cpu")]:
            test_local(src_dev, dst_dev)
        # Multi-chunk staging coverage for the host-involving paths.
        test_local("gpu", "cpu", BIG_NBYTES)
        test_local("cpu", "cpu", BIG_NBYTES)
    except KeyboardInterrupt:
        print("\nInterrupted, terminating…")
        sys.exit(1)
