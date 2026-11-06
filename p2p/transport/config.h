#pragma once
#include "util/device/backend.h"

// Build availability, not a claim about the installed driver or hardware.
// Profiles may disable optional transports without changing engine code.
#ifndef UCCL_P2P_ENABLE_CXI
#define UCCL_P2P_ENABLE_CXI (!UCCL_DEVICE_RDMA_ONLY)
#endif
#ifndef UCCL_P2P_ENABLE_EFA
#define UCCL_P2P_ENABLE_EFA (!UCCL_DEVICE_RDMA_ONLY)
#endif
// Verbs-free IPC-only build (p2p/make: ENABLE_RDMA=0). The same fallback
// lives in util/common.h; the build passes -DUCCL_P2P_ENABLE_RDMA globally.
#ifndef UCCL_P2P_ENABLE_RDMA
#define UCCL_P2P_ENABLE_RDMA 1
#endif

#if UCCL_DEVICE_RDMA_ONLY && (UCCL_P2P_ENABLE_CXI || UCCL_P2P_ENABLE_EFA)
#error "This device backend supports only RDMA/IPC"
#endif
