DEVICE_BACKEND := musa
MUSA_HOME ?= /usr/local/musa
MUSA_LIBDIR ?= $(MUSA_HOME)/lib
DEVICE_CPPFLAGS := -DUCCL_USE_MUSA -I$(MUSA_HOME)/include
DEVICE_LDLIBS := -L$(MUSA_LIBDIR) -lmusart -lmusa -Wl,-rpath,$(MUSA_LIBDIR)
# MUSA is an RDMA/IPC-only device backend and the ibverbs data plane was
# removed from this tree, so this profile can no longer build.
$(error PROFILE=musa is unsupported: the ibverbs RDMA data plane was removed from p2p; RDMA-only device backends have no network transport left)
