#pragma once
#include "common.h"

// Transport-generic stand-in kept so NCCL/CXI adapters (which return
// SendConnection*) and engine code compile unchanged. The ibverbs (IB/RoCE)
// data plane was removed from this tree, so no send group can exist:
// uccl_resolve_send_group() returns nullptr for every transport and the
// fast-path helpers are never reachable. Every method fails closed; the only
// live caller path is `send_group == nullptr`.
class SendConnection {
 public:
  static constexpr int kPostError = -3;

  struct OneSidedBatchOp {
    void* local_addr = nullptr;
    size_t size = 0;
    MRArray const* local_mr_array = nullptr;
    FifoItem const* slot_item = nullptr;
  };

  struct RawBatchWait {
    int64_t wr_id = -1;
    size_t iov_count = 0;
  };

  int64_t post_write_or_read(std::shared_ptr<RDMASendRequest> req) {
    (void)req;
    return kPostError;
  }

  bool will_compress_write(SendType send_type, size_t msg_size,
                           CompressCtx const& compress_ctx) const {
    (void)send_type;
    (void)msg_size;
    (void)compress_ctx;
    return false;
  }

  bool can_use_raw_one_sided_batch(SendType send_type,
                                   size_t max_iov_bytes = 0) const {
    (void)send_type;
    (void)max_iov_bytes;
    return false;
  }

  bool post_write_or_read_batch(SendType send_type, OneSidedBatchOp const* ops,
                                size_t num_ops, int64_t* wr_ids,
                                RawBatchWait* waits = nullptr,
                                size_t* num_waits = nullptr) {
    (void)send_type;
    (void)ops;
    (void)num_ops;
    (void)wr_ids;
    (void)waits;
    (void)num_waits;
    return false;
  }

  bool check_completion(int64_t wr_id) {
    (void)wr_id;
    return false;
  }
};
