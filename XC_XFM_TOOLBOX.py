import os
import subprocess

def new_xfm(output_folder, fixed_image, moving_image, on_complete=None, cancel_checker=None):
    
    # Assess batch size
    if isinstance(moving_image, list):
        total_files = len(moving_image)
        
        for single_file in moving_image:
            # Check for cancellation before processing each file
            if cancel_checker and cancel_checker():
                print("Registration cancelled by user")
                return
            
            new_xfm(output_folder, fixed_image, single_file, on_complete=None, cancel_checker=cancel_checker)
        
        if on_complete:
            on_complete()
        return
    
    # Generate output prefix
    def clean_name(path):
        base = os.path.basename(path)
        if base.endswith(".nii.gz"): return base[:-7]
        elif base.endswith(".nii"): return base[:-4]
        return os.path.splitext(base)[0]

    moving_name = clean_name(moving_image)
    fixed_name = clean_name(fixed_image)
    
    output_prefix = f"{moving_name}_{fixed_name}space_"
    full_output_path = os.path.join(output_folder, output_prefix)
    
    print(f"Running ANTs on: {moving_name}")

    # Resource Allocation
    try:
        total_cores = os.cpu_count()
        if total_cores is None: total_cores = 4
    except NotImplementedError:
        total_cores = 4
    safe_threads = max(1, total_cores - 2)

    # Check for cancellation before starting
    if cancel_checker and cancel_checker():
        print("Registration cancelled by user")
        return
    
    # Run
    cmd = [
        "antsRegistrationSyN.sh",
        "-d", "3",
        "-f", fixed_image,
        "-m", moving_image,
        "-o", full_output_path,
        "-n", str(safe_threads)
    ]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Poll the process and check for cancellation
        while process.poll() is None:
            if cancel_checker and cancel_checker():
                print(f"Cancelling registration for {moving_name}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                print(f"Registration cancelled: {moving_name}")
                return
        
        # Check if process completed successfully
        if process.returncode == 0:
            print(f"Success: {moving_name}")
        else:
            stderr = process.stderr.read().decode() if process.stderr else ""
            print(f"Error on {moving_name}: {stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error on {moving_name}: {e}")
    except FileNotFoundError:
        print("Error: ANTs command not found.")
    
    # Send confirmation
    if on_complete:
        on_complete()
  

def apply_existing_xfm(output_folder, transform_files, moving_image, reference_image, on_complete=None, cancel_checker=None):

    if isinstance(transform_files, str):
        transform_list = [transform_files]
    else: 
        transform_list = [f.strip() for f in transform_files if f.strip()]

    if isinstance(moving_image, list):
        for single_image in moving_image:
            # Check for cancellation before processing each image
            if cancel_checker and cancel_checker():
                print("Transform application cancelled by user")
                return
            
            apply_existing_xfm(output_folder, transform_list, single_image, reference_image, on_complete=None, cancel_checker=cancel_checker)
        if on_complete: 
            on_complete()
        return

    def clean_name(path):
        base = os.path.basename(path)
        if base.endswith(".nii.gz"):
            return base[:-7]
        elif base.endswith(".nii"):
            return base[:-4]
        return os.path.splitext(base)[0]
    
    moving_name = clean_name(moving_image)
    
    if len(transform_list) == 1:
        transform_name = clean_name(transform_list[0])
    else:
        transform_name = f"{len(transform_list)}transforms"
    
    output_filename = f"{moving_name}_applied_{transform_name}.nii.gz"
    full_output_path = os.path.join(output_folder, output_filename)

    cmd = [
        "antsApplyTransforms",
        "-d", "3",
        "-i", moving_image,
        "-r", reference_image,
        "-o", full_output_path,
        "-n", "Linear"
    ]
    
    for transform in reversed(transform_list):
        cmd.extend(["-t", transform])
    
    # Check for cancellation before starting
    if cancel_checker and cancel_checker():
        print("Transform application cancelled by user")
        return

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Poll the process and check for cancellation
        while process.poll() is None:
            if cancel_checker and cancel_checker():
                print(f"Cancelling transform application for {moving_name}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                print(f"Transform application cancelled: {moving_name}")
                return
        
        # Check if process completed successfully
        if process.returncode != 0:
            stderr = process.stderr.read().decode() if process.stderr else ""
            print(f"ANTs Apply Transforms failed with error: {stderr}")
    except subprocess.CalledProcessError as e: 
        print(f"ANTs Apply Transforms failed with error: {e}")
    except FileNotFoundError: 
        print("ANTs not found. Please ensure ANTs is in your system PATH.")

    if on_complete:
        on_complete()