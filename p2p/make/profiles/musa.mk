DEVICE_BACKEND := musa
MUSA_HOME ?= /usr/local/musa
MUSA_LIBDIR ?= $(MUSA_HOME)/lib
DEVICE_CPPFLAGS := -DUCCL_USE_MUSA -I$(MUSA_HOME)/include
DEVICE_LDLIBS := -L$(MUSA_LIBDIR) -lmusart -lmusa -Wl,-rpath,$(MUSA_LIBDIR)
# MUSA is an RDMA/IPC-only device backend: the verbs data plane stays in even
# though ENABLE_RDMA now defaults to 0.
ifeq ($(origin ENABLE_RDMA),command line)
ifneq ($(ENABLE_RDMA),1)
$(error PROFILE=musa requires ENABLE_RDMA=1 (RDMA/IPC-only device backend))
endif
endif
ENABLE_RDMA := 1
ENABLE_NCCL := 0
ENABLE_CXI := 0
ENABLE_EFA := 0
