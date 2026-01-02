import os
import subprocess
from pathlib import Path

def launch_freeview(input_images, working_dir=None, on_complete=None, cancel_checker=None):
    """
    Launch FreeSurfer's freeview with specified input images
    
    Args:
        input_images: List of image paths to open in freeview
        working_dir: Working directory (optional, used for context)
        on_complete: Callback function to call when complete
        cancel_checker: Function that returns True if task should be cancelled
    """
    # Check for cancellation
    if cancel_checker and cancel_checker():
        print("Freeview launch cancelled by user")
        return
    
    if not input_images:
        print("No input images specified for freeview")
        if on_complete:
            on_complete()
        return
    
    # Build freeview command
    cmd = ["freeview"]
    
    for img_path in input_images:
        img_path = img_path.strip()
        if img_path and os.path.exists(img_path):
            cmd.append(img_path)
    
    if len(cmd) == 1:  # Only "freeview" in command, no valid images
        print("No valid images found to display in freeview")
        if on_complete:
            on_complete()
        return
    
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


def run_recon_all(input_image, subject_id, output_dir, license_file=None, on_complete=None, cancel_checker=None):
    """
    Run FreeSurfer's recon-all pipeline
    
    Args:
        input_image: Path to input T1 image
        subject_id: Subject identifier
        output_dir: Output (subjects) directory
        license_file: Path to FreeSurfer license file
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
    
    # Build recon-all command
    cmd = [
        "recon-all",
        "-i", input_image,
        "-s", subject_id,
        "-all"
    ]
    
    print(f"Running recon-all for subject: {subject_id}")
    print(f"Input: {input_image}")
    print(f"Output directory: {output_dir}")
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


def run_fastsurfer(input_image, subject_id, output_dir, fastsurfer_home=None, license_file=None, on_complete=None, cancel_checker=None):
    """
    Run FastSurfer pipeline (FreeSurfer alternative using deep learning)
    
    Args:
        input_image: Path to input T1 image
        subject_id: Subject identifier
        output_dir: Output (subjects) directory
        fastsurfer_home: Path to FastSurfer installation
        license_file: Path to FreeSurfer license file
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
        "--sd", output_dir
    ])
    
    print(f"Running FastSurfer for subject: {subject_id}")
    print(f"Input: {input_image}")
    print(f"Output directory: {output_dir}")
    print("This may take 30-60 minutes...")
    
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
