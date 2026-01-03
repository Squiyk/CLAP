# Welcome to the CONNECT Lab's Analysis Pipeline (CLAP) Repository

CLAP is a unified platform designed to simplify the use of commonly employed neuroimaging tools, streamline research pipelines, and integrate custom-built utilities into a single, cohesive application.

## Toolboxes

### Registration Toolbox (ANTs)
- **Compute New Registration**: Batch processing of image registrations into a selected target space using ANTs SyN.
- **Apply Existing Transforms**: Batch application of precomputed spatial transforms.

### Connectome Toolbox
- **Generate Connectomes**: Generate connectivity matrices from tractograms using a specified parcellation.
- **Z-Score Connectomes**: Visualize deviations of a connectome relative to a control cohort.
- **Visualize Connectomes**: Display and compare selected connectomes.

### ROI Toolbox
- **Generate Custom sEEG Parcellation**: Create parcellation images using sEEG electrode coordinates and a corresponding reference image.

### Segmentation Toolbox (FreeSurfer / FastSurfer)
- **Launch Freeview**: Visualize MRI data with optional preloaded overlays.
- **Run recon-all**: Execute the full FreeSurfer cortical reconstruction pipeline with automatic multi-core optimization.
- **Run FastSurfer**: Perform fast deep learning–based segmentation with optional GPU acceleration.

### Script Repository
- **Import Scripts**: Centralize Python, Bash, R, MATLAB, and other scripts.
- **Organize by Project**: Categorize scripts with metadata including description, dependencies, and author.
- **Quick Discovery**: Filter and search scripts by project, language, author, or keywords.
- **One-Click Execution**: Run scripts directly in a terminal or open them in VS Code for editing.
- **Code Preview**: Inspect script contents prior to execution.

## Getting Started

To get started with CLAP:

1. Navigate to your chosen installation directory  
   (`cd your/installation/folder`)
2. Clone the repository  
   (`git clone https://github.com/Squiyk/CLAP`)
3. Navigate into the project directory  
   (`cd CLAP`)
4. Make the setup script executable (macOS/Linux)  
   (`chmod +x START_CLAP_MAC_LINUX.sh`)
5. Launch the application to initialize its environment  
   (`./START_CLAP_MAC_LINUX.sh`)
6. To update CLAP after new commits, navigate to the `CLAP` directory and run  
   (`git pull`)

Alternatively, you may download the repository as a ZIP archive from GitHub, extract it, and follow steps 4 and 5.

Within the application’s settings, you can view which external dependencies were detected on your system’s PATH and manually specify custom paths for any that were not automatically found.

## External Dependencies

CLAP relies on the following external tools:

- **ANTs** (Advanced Normalization Tools) — required for image registration
- **MRtrix3** — required for tractography and connectome generation
- **FreeSurfer** — required for cortical reconstruction and visualization (license required)
- **FastSurfer** — optional alternative for accelerated deep learning–based segmentation
