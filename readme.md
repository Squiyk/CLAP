# Welcome the the CONNECT Lab's Analysis Pipeline (CLAP) Repository

CLAP is designed as a tool to simplify usage of common tools used in brain research, streamline project pipelines and compile custom made tools into a singular package.

## Features

- **Registration Tools**: ANTs-based image registration and transform application
- **Connectome Toolbox**: Generate and analyze structural connectomes from tractography
- **ROI Parcelation Toolbox**: Generate ROI masks from SEEG coordinates
- **Segmentation Toolbox**: FreeSurfer and FastSurfer integration
- **Script Repository**: Organize, discover, and execute lab scripts from Python, Bash, R, Matlab, and more

## Toolboxes

### Segmentation Toolbox (FreeSurfer/FastSurfer)
- **Launch Freeview**: Visualize MRI data (with or without pre-loaded images)
- **Run recon-all**: Complete FreeSurfer cortical reconstruction pipeline with automatic multi-core optimization
- **Run FastSurfer**: Fast deep learning-based segmentation alternative with GPU acceleration support

### Script Repository
- **Import Scripts**: Add Python, Bash, R, Matlab, and other scripts to a centralized repository
- **Organize by Project**: Categorize scripts by project with metadata including description, dependencies, and author
- **Quick Discovery**: Filter and search scripts by project, language, author, or keywords
- **One-Click Execution**: Run scripts directly in a terminal window or open them in VS Code for editing
- **Code Preview**: View script contents before execution

## Getting Started

To get started with CLAP:

1. Navigate to your chosen installation directory  
   (`cd your/installation/folder`)
2. Clone the repository  
   (`git clone https://github.com/Squiyk/CLAP`)
3. Navigate into the project directory  
   (`cd CLAP`)
4. Make the setup script executable (Mac/Linux)  
   (`chmod +x START_CLAP_MAC_LINUX.sh`)
5. Launch the application to initialize its environment  
   (`./START_CLAP_MAC_LINUX.sh`)
6. To update CLAP after new commits, navigate to the `CLAP` directory and run  
   (`git pull`)

Alternatively, you can download the code as a ZIP archive from the GitHub repository, extract it, and follow steps 4 and 5.

In the application’s settings, you can view which external dependencies were detected on your system’s PATH and manually specify custom paths for any that were not automatically found.


## External Dependencies

CLAP requires the following external tools:
- **ANTs** (Advanced Normalization Tools) for image registration
- **MRtrix3** for tractography and connectome generation
- **FreeSurfer** for cortical reconstruction and visualization (requires license)
- **FastSurfer** (optional) for faster deep learning-based segmentation

You can check their installation status in the Settings menu within the application.