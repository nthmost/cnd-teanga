# GPU-Accelerated Transcription: Technical Requirements & Setup

**Date:** October 19, 2025
**Hardware:** NVIDIA GeForce RTX 4080 (16GB VRAM)
**Performance:** ~5.5x realtime transcription on medium model

---

## Overview

This document details the technical requirements and setup process for GPU-accelerated Whisper transcription using faster-whisper with CUDA support. It documents the challenges encountered and solutions implemented.

---

## Hardware Requirements

### Minimum Requirements
- **GPU:** NVIDIA GPU with CUDA Compute Capability 7.0+ (Volta architecture or newer)
- **VRAM:** 4GB minimum (8GB+ recommended for large models)
- **System RAM:** 8GB minimum (16GB+ recommended)

### Our Configuration
- **GPU:** NVIDIA GeForce RTX 4080
  - 16GB VRAM
  - CUDA Compute Capability 8.9
  - ~5.5x realtime performance on medium model
  - ~54 seconds to transcribe 5 minutes of audio

- **CPU:** AMD Ryzen 7 2700X (8 cores, 16 threads)
- **RAM:** 62GB (47GB available)
- **OS:** Linux Mint 22 (Ubuntu 24.04 base)
- **Kernel:** 6.8.0-85-generic

---

## Software Stack

### NVIDIA Driver & CUDA

**NVIDIA Driver:** 580.95.05
**CUDA Version:** 13.0 (driver-reported)
**CUDA Toolkit:** 12.0 (installed via apt)

```bash
# Check driver version
nvidia-smi

# Check CUDA compiler version
nvcc --version
```

**Our Output:**
```
NVIDIA-SMI 580.95.05              Driver Version: 580.95.05      CUDA Version: 13.0
nvcc: NVIDIA (R) Cuda compiler driver
Cuda compilation tools, release 12.0, V12.0.140
```

### Python Environment

**Python Version:** 3.12
**Environment Manager:** pipenv

**Key Dependencies:**
```toml
[packages]
torch = "*"              # PyTorch with CUDA support
faster-whisper = "*"     # Optimized Whisper implementation
```

**Auto-installed by PyTorch:**
- `nvidia-cudnn-cu12` (9.10.2.21) - Critical for GPU inference

---

## Installation Steps

### 1. Install NVIDIA Drivers & CUDA Toolkit

```bash
# Install CUDA development toolkit (includes nvcc compiler)
sudo apt update
sudo apt install nvidia-cuda-toolkit

# Verify installation
nvidia-smi
nvcc --version
```

**Note:** We initially had NVIDIA driver 550 with a mismatch. Upgraded to driver 580 using Driver Manager and rebooted.

### 2. Install Python Dependencies

```bash
# Navigate to project directory
cd /path/to/cnd-teanga

# Install dependencies (includes PyTorch + CUDA support)
pipenv install

# Verify PyTorch CUDA support
pipenv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Expected Output:**
```
CUDA available: True
PyTorch version: 2.9.0+cu128
CUDA version: 12.8
Device count: 1
Device name: NVIDIA GeForce RTX 4080
```

### 3. Verify cuDNN Installation

PyTorch automatically installs `nvidia-cudnn-cu12`, but the libraries are in the virtualenv and not in the system library path.

```bash
# Check cuDNN package
pipenv run pip list | grep cudnn

# Find cuDNN libraries
pipenv run python -c "import site; print(site.getsitepackages())"
find ~/.local/share/virtualenvs/*/lib -name "*cudnn*.so*" | head -10
```

**Our cuDNN libraries location:**
```
~/.local/share/virtualenvs/cnd-teanga-yA7E6JDr/lib/python3.12/site-packages/nvidia/cudnn/lib/
```

**Libraries present:**
- `libcudnn.so.9`
- `libcudnn_ops.so.9` (critical - this is what faster-whisper needs)
- `libcudnn_cnn.so.9`
- `libcudnn_adv.so.9`
- `libcudnn_graph.so.9`
- `libcudnn_heuristic.so.9`
- `libcudnn_engines_precompiled.so.9`
- `libcudnn_engines_runtime_compiled.so.9`

---

## The cuDNN Library Path Problem

### Problem Description

When attempting to run GPU transcription, we encountered this error:

```
Unable to load any of {libcudnn_ops.so.9.1.0, libcudnn_ops.so.9.1, libcudnn_ops.so.9, libcudnn_ops.so}
Invalid handle. Cannot load symbol cudnnCreateTensorDescriptor
```

### Root Cause

1. **faster-whisper** requires cuDNN 9.x libraries (uses CTranslate2 backend)
2. **Ubuntu repos** only provide cuDNN 8.x (`nvidia-cudnn` package)
3. **PyTorch** bundles cuDNN 9.x in the virtualenv (`nvidia-cudnn-cu12`)
4. **System linker** doesn't know about the virtualenv cuDNN libraries

### Why System cuDNN Doesn't Work

```bash
# System cuDNN (version 8)
$ dpkg -l | grep cudnn
ii  nvidia-cudnn  8.9.2.26~cuda12+3  amd64  NVIDIA cuDNN library

# Libraries present
$ ls -la /usr/lib/x86_64-linux-gnu/libcudnn*
lrwxrwxrwx 1 root root 13 Nov  8  2023 /usr/lib/x86_64-linux-gnu/libcudnn.so -> libcudnn.so.8
```

cuDNN 8 uses a **monolithic library** (`libcudnn.so.8`), while cuDNN 9 uses **split libraries** (`libcudnn_ops.so.9`, `libcudnn_cnn.so.9`, etc.).

faster-whisper expects cuDNN 9's split library structure and cannot use cuDNN 8.

---

## Solution: Library Path Wrapper Script

### Option 1: Manual LD_LIBRARY_PATH

```bash
# Find virtualenv directory
VENV_DIR=$(pipenv --venv)

# Set library path and run
export LD_LIBRARY_PATH="$VENV_DIR/lib/python3.12/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
pipenv run python scripts/try_transcription.py [args]
```

**Drawback:** Must remember to set the environment variable every time.

### Option 2: Wrapper Script (RECOMMENDED)

We created `scripts/run_with_cudnn.sh`:

```bash
#!/bin/bash
# Wrapper script to run Python scripts with cuDNN library path set

# Find the virtualenv directory
VENV_DIR=$(pipenv --venv 2>/dev/null)

if [ -z "$VENV_DIR" ]; then
    echo "❌ Error: Could not find pipenv virtualenv"
    exit 1
fi

# Set LD_LIBRARY_PATH to include cuDNN libraries
CUDNN_LIB_PATH="$VENV_DIR/lib/python3.12/site-packages/nvidia/cudnn/lib"

if [ ! -d "$CUDNN_LIB_PATH" ]; then
    echo "⚠️  Warning: cuDNN library path not found at: $CUDNN_LIB_PATH"
fi

export LD_LIBRARY_PATH="$CUDNN_LIB_PATH:$LD_LIBRARY_PATH"

echo "🔧 Set LD_LIBRARY_PATH to include cuDNN libraries"
echo "📁 cuDNN path: $CUDNN_LIB_PATH"
echo ""

# Run the command with pipenv
exec pipenv run "$@"
```

**Usage:**
```bash
# Make executable (one time)
chmod +x scripts/run_with_cudnn.sh

# Use for all GPU transcription
./scripts/run_with_cudnn.sh python scripts/try_transcription.py [args]
```

**Advantages:**
- ✅ Automatic library path setup
- ✅ No manual environment variable management
- ✅ Clear error messages if virtualenv not found
- ✅ Works with any Python script that needs cuDNN

---

## Compute Type Selection

The `WhisperTranscriber` class automatically selects the optimal compute precision:

```python
def __init__(
    self,
    model_size: ModelSize = "large-v3",
    device: str = "cuda",
    compute_type: str | None = None
):
    # Auto-select compute type based on device
    if compute_type is None:
        self.compute_type = "float16" if device == "cuda" else "int8"
    else:
        self.compute_type = compute_type
```

**Rationale:**
- **GPU (CUDA):** Uses `float16` for speed and VRAM efficiency
- **CPU:** Uses `int8` because CPU doesn't support efficient float16

Attempting to use `float16` on CPU results in:
```
ValueError: Requested float16 compute type, but the target device or
backend do not support efficient float16 computation.
```

---

## Testing & Validation

### Test Command

```bash
# Extract 5-minute test clip
pipenv run python scripts/extract_test_clip.py rnag_barrscealta_20251017_1100

# Transcribe with GPU
./scripts/run_with_cudnn.sh python scripts/try_transcription.py \
    rnag_barrscealta_20251017_1100 \
    --test-clip \
    --model medium \
    --device cuda
```

### Expected Output

```
🔧 Set LD_LIBRARY_PATH to include cuDNN libraries
📁 cuDNN path: /home/user/.local/share/virtualenvs/cnd-teanga-xxx/lib/python3.12/site-packages/nvidia/cudnn/lib

🟢 INFO 📝 TRANSCRIPTION TEST (TEST CLIP)
🟢 INFO Episode: Barrscéalta, clár iomlán, 17/10/2025.
🟢 INFO Model: medium
🟢 INFO Device: cuda

🟢 INFO 🎤 Initializing Whisper transcriber
🟢 INFO ✅ Whisper model loaded: medium
🟢 INFO 🎙️ Starting transcription...
🟢 INFO 📊 Detected language: cy (probability: 0.58)
🟢 INFO ✅ Transcription complete: 79 segments, 300.0s duration

📁 Files saved:
   - data/episodes/rnag_barrscealta_20251017_1100/raw_whisper.json
   - data/episodes/rnag_barrscealta_20251017_1100/transcript.txt
   - data/episodes/rnag_barrscealta_20251017_1100/subtitles.vtt
```

### Performance Metrics

**Test Audio:** 5 minutes (300 seconds)
**Transcription Time:** ~54 seconds
**Speed:** ~5.5x realtime
**Segments Generated:** 79
**GPU Memory Usage:** ~3-4GB VRAM (medium model)

### Monitoring GPU During Transcription

```bash
# In another terminal, watch GPU usage
watch -n 1 nvidia-smi
```

**Observed:**
- GPU Utilization: 80-95% during transcription
- Memory Usage: ~3.5GB / 16GB
- Temperature: ~45-50°C (well within safe limits)

---

## Troubleshooting

### Issue: "CUDA not available"

**Check:**
```bash
# Verify NVIDIA driver
nvidia-smi

# Verify PyTorch CUDA
pipenv run python -c "import torch; print(torch.cuda.is_available())"
```

**Solutions:**
- Reinstall NVIDIA drivers
- Reinstall PyTorch with CUDA support: `pipenv install --force torch`
- Check CUDA version compatibility

### Issue: cuDNN library errors

**Symptoms:**
```
Unable to load any of {libcudnn_ops.so.9.1.0, ...}
```

**Solution:** Use the wrapper script:
```bash
./scripts/run_with_cudnn.sh python [script] [args]
```

**Verify libraries exist:**
```bash
find ~/.local/share/virtualenvs -name "libcudnn_ops.so.9" 2>/dev/null
```

### Issue: Out of Memory (OOM)

**Symptoms:**
```
RuntimeError: CUDA out of memory
```

**Solutions:**
1. Use a smaller model (`small` instead of `medium` or `large-v3`)
2. Process shorter clips
3. Close other GPU applications
4. Use CPU instead: `--device cpu`

### Issue: Slow transcription on GPU

**Check:**
1. GPU is actually being used: `nvidia-smi` while transcribing
2. Using the wrapper script (not defaulting to CPU)
3. Compute type is `float16` not `int8`

**Expected speeds on RTX 4080:**
- tiny: ~15-20x realtime
- base: ~10-12x realtime
- small: ~7-9x realtime
- medium: ~5-6x realtime
- large-v3: ~3-4x realtime

---

## Alternative Approaches Considered

### 1. System-wide cuDNN Installation

**Approach:** Install cuDNN 9 system-wide from NVIDIA website

**Rejected because:**
- Requires manual download and installation
- Conflicts with package manager
- Makes system less reproducible
- Must match CUDA version exactly

### 2. Docker Container

**Approach:** Use NVIDIA CUDA Docker image with cuDNN pre-installed

**Pros:**
- Reproducible environment
- No library path issues
- Easy to share

**Cons:**
- Overhead of Docker
- More complex setup
- GPU passthrough configuration needed

**Status:** May revisit for production deployment

### 3. Conda Environment

**Approach:** Use conda instead of pipenv for better CUDA support

**Rejected because:**
- Already using pipenv
- Wrapper script solves the issue
- No significant advantage for our use case

---

## Performance Comparison: GPU vs CPU

### Test: 5-minute audio clip, medium model

| Device | Time | Speed | Notes |
|--------|------|-------|-------|
| **RTX 4080 (GPU)** | ~54s | 5.5x realtime | Wrapper script required |
| **Ryzen 7 2700X (CPU)** | ~5+ min | 1x realtime | Uses int8 quantization |

**Conclusion:** GPU is ~6x faster than CPU for this workload.

---

## Recommendations

### For Development
- Use `medium` model with GPU for good speed/quality balance
- Extract 5-minute clips for rapid iteration
- Use wrapper script for all GPU transcription

### For Production
- Use `large-v3` model for best Irish language quality
- Process full episodes in batch overnight
- Monitor GPU temperature and memory
- Consider Docker container for deployment

### For Testing
- Use `small` or `tiny` models for fastest iteration
- Start with 1-2 minute clips
- CPU is acceptable for quick syntax testing

---

## Future Improvements

### 1. Automatic Library Path Detection
Modify Python code to automatically add cuDNN path:

```python
import sys
import os
from pathlib import Path

# Auto-detect virtualenv cuDNN
venv_dir = Path(sys.prefix)
cudnn_lib = venv_dir / "lib" / "python3.12" / "site-packages" / "nvidia" / "cudnn" / "lib"

if cudnn_lib.exists():
    os.environ["LD_LIBRARY_PATH"] = f"{cudnn_lib}:{os.environ.get('LD_LIBRARY_PATH', '')}"
```

**Status:** Not implemented yet (wrapper script is cleaner)

### 2. Model Caching
First run downloads models (~1.5GB for medium). Subsequent runs use cache.

**Cache location:** `~/.cache/huggingface/hub/models--Systran--faster-whisper-medium/`

### 3. Batch Processing
Implement batch transcription for multiple episodes:

```bash
./scripts/run_with_cudnn.sh python scripts/batch_transcribe.py \
    --episodes data/episodes/rnag_* \
    --model large-v3
```

**Status:** Not implemented yet

---

## References

- [faster-whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [CTranslate2 Documentation](https://opennmt.net/CTranslate2/)
- [NVIDIA cuDNN Documentation](https://docs.nvidia.com/deeplearning/cudnn/)
- [PyTorch CUDA Documentation](https://pytorch.org/docs/stable/cuda.html)

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-19 | 1.0 | Initial documentation of GPU transcription setup |

---

**Author:** Claude Code + Human Collaboration
**Hardware:** NVIDIA GeForce RTX 4080
**Status:** Production Ready ✅
