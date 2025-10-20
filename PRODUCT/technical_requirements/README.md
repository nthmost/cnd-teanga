# Technical Requirements Documentation

This directory contains detailed technical documentation for system requirements, setup procedures, and infrastructure decisions for the cnd-teanga project.

---

## Table of Contents

### Hardware & Infrastructure

#### [GPU-Accelerated Transcription](transcription_GPU.md)
**Status:** ✅ Complete | **Last Updated:** October 19, 2025

Comprehensive guide to setting up GPU-accelerated Whisper transcription with faster-whisper and CUDA.

**Topics Covered:**
- Hardware requirements (NVIDIA GPU, VRAM, system specs)
- NVIDIA driver and CUDA toolkit installation
- cuDNN library path configuration
- PyTorch with CUDA support
- The cuDNN library path problem and wrapper script solution
- Performance benchmarks (RTX 4080: ~5.5x realtime)
- Troubleshooting guide
- GPU vs CPU performance comparison

**Key Takeaway:** GPU transcription requires a wrapper script to set library paths due to cuDNN 9 being in the virtualenv rather than system-wide.

---

### Coming Soon

#### Conductor OSS Setup
**Status:** 🔄 Planned

Requirements and setup for running Orkes Conductor (OSS version) for workflow orchestration.

**Planned Topics:**
- Docker Compose configuration
- Database setup (PostgreSQL, Elasticsearch)
- Worker registration
- Task queue configuration
- Monitoring and observability

#### Claude API Integration
**Status:** 🔄 Planned

Technical requirements for Claude API integration for Irish language normalization.

**Planned Topics:**
- API key management
- Rate limiting and quota management
- Prompt engineering for Irish normalization
- Cost estimation
- Error handling and retry strategies

#### OpenAI API Integration
**Status:** 🔄 Planned

Alternative/complementary AI service for comparison and failover.

**Planned Topics:**
- GPT-4 API setup
- Model selection (GPT-4 vs GPT-3.5-turbo)
- Cost comparison with Claude
- Quality benchmarking

#### Storage Requirements
**Status:** 🔄 Planned

Data storage considerations for episode artifacts and metadata.

**Planned Topics:**
- Local storage requirements (per episode, scaling)
- S3/GCS integration for cloud storage
- Backup strategies
- Episode cleanup and archival

#### Development Environment
**Status:** 🔄 Planned

Complete development environment setup guide.

**Planned Topics:**
- Python 3.12 environment setup
- pipenv best practices
- FFmpeg installation
- Git LFS for large files
- VS Code / IDE configuration

---

## Quick Reference

### Current System Requirements

**Minimum:**
- Python 3.12+
- 8GB RAM
- FFmpeg installed
- 50GB storage for testing

**Recommended (with GPU):**
- NVIDIA GPU (8GB+ VRAM)
- 16GB+ RAM
- CUDA 12.0+
- 500GB storage for production

**Our Development System:**
- GPU: NVIDIA GeForce RTX 4080 (16GB VRAM)
- CPU: AMD Ryzen 7 2700X (8 cores)
- RAM: 62GB
- OS: Linux Mint 22 (Ubuntu 24.04 base)

---

## Document Status Legend

- ✅ **Complete** - Fully documented and tested
- 🔄 **Planned** - Scheduled for documentation
- ⚠️ **Draft** - Work in progress
- 🔧 **Needs Update** - Outdated, requires revision

---

## Contributing to This Documentation

When adding new technical requirements documentation:

1. **Create a descriptive filename:** Use lowercase with underscores (e.g., `conductor_setup.md`)
2. **Follow the template structure:**
   - Overview
   - Requirements (hardware/software)
   - Installation steps
   - Configuration
   - Testing & validation
   - Troubleshooting
   - Performance notes
   - References

3. **Update this README:**
   - Add entry to Table of Contents
   - Include status, date, and key takeaway
   - Update Quick Reference if needed

4. **Use clear headings:** Make it easy to scan and find information

5. **Include commands:** Provide copy-paste-ready shell commands

6. **Document failures:** What didn't work and why (helps others avoid same mistakes)

---

## Related Documentation

- [PRODUCT/iteration_1.md](../iteration_1.md) - Initial architecture decisions
- [PRODUCT/checkpoint_iteration2_transcription.md](../checkpoint_iteration2_transcription.md) - Transcription implementation
- [PRODUCT/poc_gaeilge.md](../poc_gaeilge.md) - Original POC vision
- [CLAUDE.md](../../CLAUDE.md) - Code standards and collaboration guidelines
- [README.md](../../README.md) - Project overview and quick start

---

**Last Updated:** October 19, 2025
