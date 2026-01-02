# Welcome the the CONNECT Lab's Analysis Pipeline (CLAP) Repository

CLAP is designed as a tool to simplify usage of common tools used in brain research, streamline project pipelines and compile custom made tools into a singular package.

## Features

- **Registration Tools**: ANTs-based image registration and transform application
- **Connectome Toolbox**: Generate and analyze structural connectomes from tractography
- **ROI Parcelation Toolbox**: Generate ROI masks from SEEG coordinates
- **Segmentation Toolbox**: FreeSurfer and FastSurfer integration for cortical reconstruction
- **Settings Menu**: Check installation status of external dependencies
- **Task History**: Complete log of all tasks with input files and output locations
- **Persistent Menus**: Application remembers your last page and menu state
- **Task Control**: Cancel running tasks and view progress indicators

## Toolboxes

### Segmentation Toolbox (FreeSurfer/FastSurfer)
- **Launch Freeview**: Visualize MRI data (with or without pre-loaded images)
- **Run recon-all**: Complete FreeSurfer cortical reconstruction pipeline
- **Run FastSurfer**: Fast deep learning-based segmentation alternative
- **Auto-fill Subject IDs**: Automatically extract subject ID from filenames

## Getting Started

To get started with CLAP, download the code as a zip folder and run the configuration script. 
You may need to update it's permissions using chmod +x before doing so.

## External Dependencies

CLAP requires the following external tools:
- **ANTs** (Advanced Normalization Tools) for image registration
- **MRtrix3** for tractography and connectome generation
- **FreeSurfer** for cortical reconstruction and visualization (requires license)
- **FastSurfer** (optional) for faster deep learning-based segmentation

You can check their installation status in the Settings menu within the application.