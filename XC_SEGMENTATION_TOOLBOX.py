import os
import subprocess
from pathlib import Path

def extract_subject_id_from_filename(filepath):
    """
    Extract subject ID from filename by taking the first part before underscore or hyphen.
    
    Examples:
        sub-01_trial_ses-01_T1w.nii -> sub-01
        subject001_T1.nii.gz -> subject001
        patient-123_session1_T1w.nii -> patient-123
    
    Args:
        filepath: Path to the file
    
    Returns:
        Subject ID string (first part of filename before _ or entire filename if no separator)
    """
    if not filepath:
        return ""
    
    # Get filename without extension
    filename = Path(filepath).name
    
    # Remove common extensions
    for ext in ['.nii.gz', '.nii', '.mgz']:
        if filename.endswith(ext):
            filename = filename[:-len(ext)]
            break
    
    # Split by underscore and take first part
    if '_' in filename:
        return filename.split('_')[0]
    
    # If no underscore, return the whole filename
    return filename


def launch_freeview(input_images, working_dir=None, on_complete=None, cancel_checker=None):
    """
    Launch FreeSurfer's freeview with specified input images
    
    Args:
        input_images: List of image paths to open in freeview (can be empty to launch without images)
        working_dir: Working directory (optional, used for context)
        on_complete: Callback function to call when complete
        cancel_checker: Function that returns True if task should be cancelled
    """
    # Check for cancellation
    if cancel_checker and cancel_checker():
        print("Freeview launch cancelled by user")
        return
    
    # Build freeview command
    cmd = ["freeview"]
    
    # Add images if provided
    if input_images:
        for img_path in input_images:
            img_path = img_path.strip()
            if img_path and os.path.exists(img_path):
                cmd.append(img_path)
    
    # Launch freeview even without images (user can load manually)
    if len(cmd) == 1:
        print("Launching freeview without pre-loaded images (load manually)...")
    else:
        print(f"Launching freeview with {len(cmd)-1} image(s)...")
    
    try:
        # Launch freeview as a detached process
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print("Freeview launched successfully")
    except FileNotFoundError:
        print("ERROR: freeview command not found. Please ensure FreeSurfer is installed and in your PATH.")
    except Exception as e:
        print(f"ERROR launching freeview: {e}")
    
    if on_complete:
        on_complete()


def run_recon_all(input_image, subject_id, output_dir, license_file=None, num_threads=None, on_complete=None, cancel_checker=None):
    """
    Run FreeSurfer's recon-all pipeline
    
    Args:
        input_image: Path to input T1 image
        subject_id: Subject identifier
        output_dir: Output (subjects) directory
        license_file: Path to FreeSurfer license file
        num_threads: Number of threads to use (None for auto-detect safe maximum)
        on_complete: Callback function to call when complete
        cancel_checker: Function that returns True if task should be cancelled
    """
    # Check for cancellation at start
    if cancel_checker and cancel_checker():
        print("Recon-all cancelled by user")
        return
    
    if not input_image or not subject_id or not output_dir:
        print("ERROR: Missing required parameters for recon-all")
        if on_complete:
            on_complete()
        return
    
    # Prepare environment
    env = os.environ.copy()
    
    # Set SUBJECTS_DIR
    env['SUBJECTS_DIR'] = output_dir
    
    # Set license file if provided
    if license_file and os.path.exists(license_file):
        env['FS_LICENSE'] = license_file
        print(f"Using FreeSurfer license: {license_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate number of threads if not provided
    if num_threads is None:
        try:
            total_cores = os.cpu_count()
            if total_cores is None:
                total_cores = 4
        except NotImplementedError:
            total_cores = 4
        # Reserve 2 cores for system, use at least 1
        num_threads = max(1, total_cores - 2)
    
    # Build recon-all command with OpenMP threading
    cmd = [
        "recon-all",
        "-i", input_image,
        "-s", subject_id,
        "-all",
        "-openmp", str(num_threads)
    ]
    
    print(f"Running recon-all for subject: {subject_id}")
    print(f"Input: {input_image}")
    print(f"Output directory: {output_dir}")
    print(f"Using {num_threads} threads")
    print("This may take several hours...")
    
    try:
        # Run recon-all
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor process and check for cancellation
        while True:
            if cancel_checker and cancel_checker():
                print("Recon-all cancelled by user, terminating process...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                print("Recon-all process terminated")
                return
            
            # Check if process has finished
            retcode = process.poll()
            if retcode is not None:
                break
            
            # Read and print output
            line = process.stdout.readline()
            if line:
                print(line.rstrip())
        
        # Check final return code
        if retcode == 0:
            print("Recon-all completed successfully")
        else:
            print(f"Recon-all failed with return code {retcode}")
            
    except FileNotFoundError:
        print("ERROR: recon-all command not found. Please ensure FreeSurfer is installed and in your PATH.")
    except Exception as e:
        print(f"ERROR running recon-all: {e}")
    
    if on_complete:
        on_complete()


def run_fastsurfer(input_image, subject_id, output_dir, fastsurfer_home=None, license_file=None, use_gpu=True, num_threads=None, on_complete=None, cancel_checker=None):
    """
    Run FastSurfer pipeline (FreeSurfer alternative using deep learning)
    
    Args:
        input_image: Path to input T1 image
        subject_id: Subject identifier
        output_dir: Output (subjects) directory
        fastsurfer_home: Path to FastSurfer installation
        license_file: Path to FreeSurfer license file
        use_gpu: Whether to use GPU acceleration (default: True)
        num_threads: Number of threads to use for surface reconstruction (None for auto-detect)
        on_complete: Callback function to call when complete
        cancel_checker: Function that returns True if task should be cancelled
    """
    # Check for cancellation at start
    if cancel_checker and cancel_checker():
        print("FastSurfer cancelled by user")
        return
    
    if not input_image or not subject_id or not output_dir:
        print("ERROR: Missing required parameters for FastSurfer")
        if on_complete:
            on_complete()
        return
    
    # Prepare environment
    env = os.environ.copy()
    
    # Set SUBJECTS_DIR
    env['SUBJECTS_DIR'] = output_dir
    
    # Set license file if provided
    if license_file and os.path.exists(license_file):
        env['FS_LICENSE'] = license_file
        print(f"Using FreeSurfer license: {license_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate number of threads if not provided
    if num_threads is None:
        try:
            total_cores = os.cpu_count()
            if total_cores is None:
                total_cores = 4
        except NotImplementedError:
            total_cores = 4
        # Reserve 2 cores for system, use at least 1
        num_threads = max(1, total_cores - 2)
    
    # Determine FastSurfer command
    if fastsurfer_home and os.path.exists(fastsurfer_home):
        run_fastsurfer_script = os.path.join(fastsurfer_home, "run_fastsurfer.sh")
        if not os.path.exists(run_fastsurfer_script):
            print(f"ERROR: run_fastsurfer.sh not found in {fastsurfer_home}")
            if on_complete:
                on_complete()
            return
        cmd = [run_fastsurfer_script]
    else:
        # Try to find run_fastsurfer.sh in PATH
        cmd = ["run_fastsurfer.sh"]
    
    # Add FastSurfer arguments
    cmd.extend([
        "--t1", input_image,
        "--sid", subject_id,
        "--sd", output_dir,
        "--threads", str(num_threads)
    ])
    
    # Detect if running on Apple Silicon
    is_apple_silicon = False
    try:
        import platform
        if platform.system() == 'Darwin':  # macOS
            # Check if running on ARM architecture (Apple Silicon)
            machine = platform.machine()
            if machine == 'arm64':
                is_apple_silicon = True
    except Exception:
        pass
    
    # Add GPU/CPU flag
    if use_gpu:
        if is_apple_silicon:
            # Apple Silicon with MPS support
            cmd.append("--device")
            cmd.append("mps")
            env['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
            print("Using Apple Silicon GPU (MPS) with fallback enabled")
        else:
            # Standard GPU mode (CUDA)
            print("Using GPU acceleration (CUDA if available)")
    else:
        # CPU-only mode
        cmd.append("--device")
        cmd.append("cpu")
        print("Using CPU-only mode")
    
    print(f"Running FastSurfer for subject: {subject_id}")
    print(f"Input: {input_image}")
    print(f"Output directory: {output_dir}")
    print(f"Using {num_threads} threads for surface reconstruction")
    if use_gpu:
        if is_apple_silicon:
            print("This may take 30-90 minutes with Apple Silicon GPU...")
        else:
            print("This may take 30-60 minutes with GPU...")
    else:
        print("This may take 1-3 hours with CPU...")
    
    try:
        # Run FastSurfer
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor process and check for cancellation
        while True:
            if cancel_checker and cancel_checker():
                print("FastSurfer cancelled by user, terminating process...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                print("FastSurfer process terminated")
                return
            
            # Check if process has finished
            retcode = process.poll()
            if retcode is not None:
                break
            
            # Read and print output
            line = process.stdout.readline()
            if line:
                print(line.rstrip())
        
        # Check final return code
        if retcode == 0:
            print("FastSurfer completed successfully")
        else:
            print(f"FastSurfer failed with return code {retcode}")
            
    except FileNotFoundError:
        print("ERROR: FastSurfer command not found. Please ensure FastSurfer is installed and configured.")
    except Exception as e:
        print(f"ERROR running FastSurfer: {e}")
    
    if on_complete:
        on_complete()
