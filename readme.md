# Welcome the the CONNECT Lab's Analysis Pipeline (CLAP) Repository

CLAP is designed as a tool to simplify usage of common tools used in brain research, streamline project pipelines and compile custom made tools into a singular package.

## Features

- **Registration Tools**: ANTs-based image registration and transform application
- **Connectome Toolbox**: Generate and analyze structural connectomes from tractography
- **ROI Parcelation Toolbox**: Generate ROI masks from SEEG coordinates
- **Segmentation Toolbox**: FreeSurfer and FastSurfer integration for cortical reconstruction with multi-core and GPU support
- **Settings Menu**: Check installation status of external dependencies and configure FreeSurfer license
- **Task History**: Complete log of all tasks with input files and output locations
- **Persistent Menus**: Application remembers your last page and menu state
- **Task Control**: Cancel running tasks and view progress indicators
- **Performance Optimizations**: Automatic multi-core processing and GPU acceleration

## Toolboxes

### Segmentation Toolbox (FreeSurfer/FastSurfer)
- **Launch Freeview**: Visualize MRI data (with or without pre-loaded images)
- **Run recon-all**: Complete FreeSurfer cortical reconstruction pipeline with automatic multi-core optimization
- **Run FastSurfer**: Fast deep learning-based segmentation alternative with GPU acceleration support
- **Auto-fill Subject IDs**: Automatically extract subject ID from filenames
- **Performance Features**:
  - Multi-core processing: Automatically uses optimal thread count (cores - 2, minimum 1)
  - GPU acceleration: Toggle for CUDA, Apple Silicon MPS, or CPU-only processing
  - Apple Silicon support: Automatic detection and MPS backend configuration

## Getting Started

To get started with CLAP, download the code as a zip folder and run the configuration script. 
You may need to update it's permissions using chmod +x before doing so.

## Performance Optimizations

### Multi-Core Processing
CLAP automatically optimizes processing performance using available CPU cores:
- **FreeSurfer recon-all**: Uses OpenMP with automatic thread detection (cores - 2, minimum 1)
- **FastSurfer**: Multi-threaded surface reconstruction
- **Performance Gain**: 2.5-3x faster on multi-core systems (e.g., 8-core reduces 10 hours to 3-4 hours)

### GPU Acceleration
- **FastSurfer GPU Toggle**: Enable/disable GPU acceleration via UI checkbox
- **CUDA Support**: Automatic GPU detection on Linux/Windows with NVIDIA GPUs
- **Apple Silicon**: Automatic MPS (Metal Performance Shaders) support for M1/M2/M3 chips
- **CPU Fallback**: Always available when GPU is disabled or unavailable
- **Performance Gain**: 2-6x faster with GPU compared to CPU-only processing

## External Dependencies

CLAP requires the following external tools:
- **ANTs** (Advanced Normalization Tools) for image registration
- **MRtrix3** for tractography and connectome generation
- **FreeSurfer** for cortical reconstruction and visualization (requires license)
- **FastSurfer** (optional) for faster deep learning-based segmentation

You can check their installation status in the Settings menu within the application.