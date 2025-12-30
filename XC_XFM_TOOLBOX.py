import os
import subprocess

def new_xfm(n_output_folder, n_fixed_image, n_moving_image, on_complete=None):
    
    # Assess batch size
    if isinstance(n_moving_image, list):
        total_files = len(n_moving_image)
        
        for single_file in n_moving_image:
            
            new_xfm(n_output_folder, n_fixed_image, single_file, on_complete=None)
        
        if on_complete:
            on_complete()
        return
    
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

    # Run
    cmd = [
        "antsRegistrationSyN.sh",
        "-d", "3",
        "-f", n_fixed_image,
        "-m", n_moving_image,
        "-o", full_output_path,
        "-n", str(safe_threads)
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"Success: {mov_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error on {mov_name}: {e}")
    except FileNotFoundError:
        print("Error: ANTs command not found.")
    
    # Send confirmation
    if on_complete:
        on_complete()
  

def apply_existing_xfm(output_folder, xfm_files, moving_image, reference_image, on_complete=None):

    if isinstance(xfm_files, str):
        xfm_list = [xfm_files]
    else: 
        xfm_list = [f. strip() for f in xfm_files if f.strip()]

    if isinstance(moving_image, list):
        for single_image in moving_image:
            apply_existing_xfm(output_folder, xfm_list, single_image, reference_image, on_complete=None)
        if on_complete: 
            on_complete()
        return

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

    try:
        subprocess. run(cmd, check=True)
    except subprocess.CalledProcessError as e: 
        print(f"ANTs Apply Transforms failed with error: {e}")
    except FileNotFoundError: 
        print("ANTs not found. Please ensure ANTs is installed and in your system PATH.")

    if on_complete:
        on_complete()