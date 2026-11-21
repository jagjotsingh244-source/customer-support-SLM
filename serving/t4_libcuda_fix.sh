#!/usr/bin/env bash
# Make vLLM start on a Kaggle T4 (GPU risk test 3, notes/gpu-risk-tests/).
#
# Why: on first use FlashInfer compiles a norm kernel for the GPU (sm75 on a T4) and links it with -lcuda.
# Kaggle's image has the driver (/usr/local/nvidia/lib64/libcuda.so.<version>) but no plain libcuda.so,
# so the link fails with "/usr/bin/ld: cannot find -lcuda" and vLLM's engine never starts.
#
# Fix: give the linker a libcuda.so that points at the driver, through LIBRARY_PATH.
# Use it before starting vLLM:
#   source serving/t4_libcuda_fix.sh
#   vllm serve Qwen/Qwen3.5-2B ...
set -u

LINK_DIR=/tmp/cuda-link
LIBCUDA=""
for f in /usr/local/cuda*/lib64/stubs/libcuda.so /usr/lib/x86_64-linux-gnu/libcuda.so* \
         /usr/local/nvidia/lib64/libcuda.so* /usr/lib64/libcuda.so*; do
  if [ -e "$f" ]; then LIBCUDA="$f"; break; fi
done

if [ -z "$LIBCUDA" ]; then
  echo "t4_libcuda_fix: no libcuda found; vLLM's FlashInfer kernels may fail to link" >&2
else
  mkdir -p "$LINK_DIR"
  ln -sf "$(readlink -f "$LIBCUDA")" "$LINK_DIR/libcuda.so"
  export LIBRARY_PATH="$LINK_DIR${LIBRARY_PATH:+:$LIBRARY_PATH}"
  echo "t4_libcuda_fix: linking against $LIBCUDA (LIBRARY_PATH=$LIBRARY_PATH)"
fi
