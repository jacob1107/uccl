#pragma once
#include "util/device/backend.h"

// Build availability, not a claim about the installed driver or hardware.
// The ibverbs (IB/RoCE + EFA) data plane was removed from this tree, so those
// transports are permanently unavailable; the macros stay (pinned to 0) so
// callers can keep asking transport_available() uniformly.
#define UCCL_P2P_ENABLE_RDMA 0
#ifndef UCCL_P2P_ENABLE_NCCL
#define UCCL_P2P_ENABLE_NCCL (!UCCL_DEVICE_RDMA_ONLY)
#endif
#ifndef UCCL_P2P_ENABLE_CXI
#define UCCL_P2P_ENABLE_CXI (!UCCL_DEVICE_RDMA_ONLY)
#endif
#define UCCL_P2P_ENABLE_EFA 0

#if UCCL_DEVICE_RDMA_ONLY && \
    (UCCL_P2P_ENABLE_NCCL || UCCL_P2P_ENABLE_CXI || UCCL_P2P_ENABLE_EFA)
#error "This device backend supports only RDMA/IPC"
#endif
