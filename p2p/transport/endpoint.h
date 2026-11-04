#pragma once
#include "transport/config.h"
#if UCCL_P2P_ENABLE_RDMA
#include "rdma/rdma_endpoint.h"
#endif
#if UCCL_P2P_ENABLE_NCCL
#include "nccl/nccl_endpoint.h"
#endif
#if UCCL_P2P_ENABLE_CXI
#include "cxi/cxi_endpoint.h"
#endif
#include <memory>
#include <type_traits>
#include <variant>

// Memory handles may hold an empty CXI reference in builds without CXI.
struct CxiMemoryRegion;

// This is the compile-time transport registration boundary.
// Runtime-polymorphic endpoint. Each alternative emits its own leading comma
// when it is not the first enabled one, so any combination of transports
// forms a valid variant.
using GenericEndpoint = std::variant<
#if UCCL_P2P_ENABLE_RDMA
    std::shared_ptr<RDMAEndpoint>
#endif
#if UCCL_P2P_ENABLE_NCCL
#if UCCL_P2P_ENABLE_RDMA
    ,
#endif
    std::shared_ptr<NCCLEndpoint>
#endif
#if UCCL_P2P_ENABLE_CXI
#if UCCL_P2P_ENABLE_RDMA || UCCL_P2P_ENABLE_NCCL
    ,
#endif
    std::shared_ptr<CxiEndpoint>
#endif
    >;

static_assert(!std::is_same_v<GenericEndpoint, std::variant<>>,
              "No P2P transport compiled in: enable at least one of "
              "UCCL_P2P_ENABLE_RDMA/NCCL/CXI");
