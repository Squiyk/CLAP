import os
import subprocess

def new_xfm(n_output_folder, n_fixed_image, n_moving_image, on_complete=None, cancel_checker=None):
    
    # Assess batch size
    if isinstance(n_moving_image, list):
        total_files = len(n_moving_image)
        has_failures = False
        
        for single_file in n_moving_image:
            # Check for cancellation before processing each file
            if cancel_checker and cancel_checker():
                print("Registration cancelled by user")
                if on_complete:
                    on_complete(success=False)
                return
            
            # Track failures in batch processing
            # Call recursively without callback, check success manually
            result = new_xfm(n_output_folder, n_fixed_image, single_file, on_complete=None, cancel_checker=cancel_checker)
            if result is False:
                has_failures = True
        
        if on_complete:
            on_complete(success=(not has_failures))
        return not has_failures
    
    # Generate output prefix
    def clean_name(path):
        base = os.path.basename(path)
        if base.endswith(".nii.gz"): return base[:-7]
        elif base.endswith(".nii"): return base[:-4]
        return os.path.splitext(base)[0]

    mov_name = clean_name(n_moving_image)
    fix_name = clean_name(n_fixed_image)
    
    new_prefix = f"{mov_name}_{fix_name}space_"
    full_output_path = os.path.join(n_output_folder, new_prefix)
    
    print(f"Running ANTs on: {mov_name}")

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
        if on_complete:
            on_complete(success=False)
        return False
    
    # Run
    cmd = [
        "antsRegistrationSyN.sh",
        "-d", "3",
        "-f", n_fixed_image,
        "-m", n_moving_image,
        "-o", full_output_path,
        "-n", str(safe_threads)
    ]

    success = False
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Poll the process and check for cancellation
        while process.poll() is None:
            if cancel_checker and cancel_checker():
                print(f"Cancelling registration for {mov_name}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                print(f"Registration cancelled: {mov_name}")
                if on_complete:
                    on_complete(success=False)
                return False
        
        # Check if process completed successfully
        if process.returncode == 0:
            print(f"Success: {mov_name}")
            success = True
        else:
            stderr = process.stderr.read().decode() if process.stderr else ""
            print(f"Error on {mov_name}: {stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error on {mov_name}: {e}")
    except FileNotFoundError:
        print("Error: ANTs command not found.")
    
    # Send confirmation
    if on_complete:
        on_complete(success=success)
    
    return success
  

def apply_existing_xfm(output_folder, xfm_files, moving_image, reference_image, on_complete=None, cancel_checker=None):

    if isinstance(xfm_files, str):
        xfm_list = [xfm_files]
    else: 
        xfm_list = [f.strip() for f in xfm_files if f.strip()]

    if isinstance(moving_image, list):
        has_failures = False
        for single_image in moving_image:
            # Check for cancellation before processing each image
            if cancel_checker and cancel_checker():
                print("Transform application cancelled by user")
                if on_complete:
                    on_complete(success=False)
                return
            
            result = apply_existing_xfm(output_folder, xfm_list, single_image, reference_image, on_complete=None, cancel_checker=cancel_checker)
            if result is False:
                has_failures = True
        if on_complete: 
            on_complete(success=(not has_failures))
        return not has_failures

    def clean_name(path):
        base = os.path.basename(path)
        if base.endswith(".nii.gz"):
            return base[:-7]
        elif base.endswith(". nii"):
            return base[:-4]
        return os.path.splitext(base)[0]
    
    mov_name = clean_name(moving_image)
    
    if len(xfm_list) == 1:
        xfm_name = clean_name(xfm_list[0])
    else:
        xfm_name = f"{len(xfm_list)}transforms"
    
    new_name = f"{mov_name}_applied_{xfm_name}.nii.gz"
    full_output_path = os.path.join(output_folder, new_name)

    cmd = [
        "antsApplyTransforms",
        "-d", "3",
        "-i", moving_image,
        "-r", reference_image,
        "-o", full_output_path,
        "-n", "Linear"
    ]
    
    for xfm in reversed(xfm_list):
        cmd.extend(["-t", xfm])
    
    # Check for cancellation before starting
    if cancel_checker and cancel_checker():
        print("Transform application cancelled by user")
        if on_complete:
            on_complete(success=False)
        return False

    success = False
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Poll the process and check for cancellation
        while process.poll() is None:
            if cancel_checker and cancel_checker():
                print(f"Cancelling transform application for {mov_name}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                print(f"Transform application cancelled: {mov_name}")
                if on_complete:
                    on_complete(success=False)
                return False
        
        # Check if process completed successfully
        if process.returncode == 0:
            success = True
        else:
            stderr = process.stderr.read().decode() if process.stderr else ""
            print(f"ANTs Apply Transforms failed with error: {stderr}")
    except subprocess.CalledProcessError as e: 
        print(f"ANTs Apply Transforms failed with error: {e}")
    except FileNotFoundError: 
        print("ANTs not found. Please ensure ANTs is in your system PATH.")

    if on_complete:
        on_complete(success=success)
    
    return success