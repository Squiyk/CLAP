# CLAP New Features

## Settings Menu ⚙️

The Settings page allows you to:

- **Check External Dependencies**: View the installation status of required external tools:
  - ANTs (antsRegistrationSyN.sh, antsApplyTransforms)
  - MRtrix3 (tck2connectome)
- **Configure Appearance**: Change between Light, Dark, and System appearance modes
- **Refresh Status**: Update the dependency status check

### External Dependencies

CLAP requires the following external tools to be installed and available in your system PATH:

1. **ANTs (Advanced Normalization Tools)**
   - Used for: Image registration and transformation
   - Commands: `antsRegistrationSyN.sh`, `antsApplyTransforms`

2. **MRtrix3**
   - Used for: Tractography and connectome generation
   - Commands: `tck2connectome`

## Task History 📋

The History page provides a complete log of all tasks executed in CLAP:

- **Task Information**: View task name, type, status, and timing
- **Input Files**: See which files were used as input for each task
- **Output Location**: Quickly find where task results were saved
- **Status Indicators**: Color-coded status (green for completed, orange for running/interrupted, red for failed)
- **Duration**: See how long each task took to complete
- **Clear History**: Remove all task history if needed

## Persistent Menu State

CLAP now remembers your preferences across sessions:

- **Last Page**: The application reopens to the last page you were viewing
- **Menu State**: The Tools menu expansion state is preserved
- **Appearance**: Your selected appearance mode (Light/Dark/System) is saved

## Task Control

When a task is running:

- **Progress Indicator**: A progress bar appears in the sidebar showing task activity
- **Cancel Button**: Click "Cancel Task" to interrupt the current operation
- **Task Status**: See which task is currently running

## User Data

All user-specific settings and history are stored in the `user_data/` directory:

- `settings.json`: Application settings and preferences
- `task_history.json`: Complete log of all tasks

This directory is automatically created on first run and is excluded from Git tracking.

## Usage Tips

1. **Check Dependencies First**: Visit the Settings page after installation to verify all required tools are available
2. **Review Task History**: Use the History page to track your work and locate output files
3. **Cancel Long Tasks**: If a task is taking too long or was started by mistake, use the Cancel button
4. **Clear Old History**: Periodically clear task history to keep the log manageable
