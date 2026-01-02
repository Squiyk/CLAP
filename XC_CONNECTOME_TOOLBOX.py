import os
import subprocess
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

def gen_connectome(mask_image, tracks_list, output_dir, tracks_weights_list=None, on_complete=None, cancel_checker=None):

    # CREATE OUTPUT FOLDER
    mask_filename = os.path.basename(mask_image)
    mask_name_clean = mask_filename.replace(".nii", "").replace(".gz", "")
    
    output_folder = os.path.join(output_dir, f"Connectomes_{mask_name_clean}")
    os.makedirs(output_folder, exist_ok=True)

    # Run
    for track_path in tracks_list:
        # Check for cancellation before processing each track
        if cancel_checker and cancel_checker():
            print("Connectome generation cancelled by user")
            return
        
        track_path = track_path.strip()
        if not track_path or not os.path.exists(track_path):
            continue

        track_name = os.path.splitext(os.path.basename(track_path))[0]
        output_csv_path = os.path.join(output_folder, f"{track_name}_connectome.csv")

        weights_file = None

        if tracks_weights_list:
            for weight_path in tracks_weights_list:
                weight_path = weight_path.strip()
                if not weight_path:
                    continue
                weight_stem = os.path.splitext(os.path.basename(weight_path))[0]
                if weight_stem == track_name:
                    weights_file = weight_path
                    break

        cmd = [
            "tck2connectome",
            track_path,           
            mask_image,
            output_csv_path
        ]

        if weights_file:
            cmd.extend(["-tck_weights_in", weights_file])

        cmd.append("-force")


        try:
            # Check for cancellation before starting
            if cancel_checker and cancel_checker():
                print("Connectome generation cancelled by user")
                return

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Poll the process and check for cancellation
            while process.poll() is None:
                if cancel_checker and cancel_checker():
                    print(f"Cancelling connectome generation for {track_name}")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    print(f"Connectome generation cancelled: {track_name}")
                    return
            
            # Check if process completed successfully
            if process.returncode == 0:
                print(f"Created: {os.path.basename(output_csv_path)}")
            else:
                stderr = process.stderr.read() if process.stderr else ""
                print(f"Command Failed for {track_name}:\n{stderr}")
                
        except Exception as e:
            print(f"Critical Error on {track_name}: {e}")

    print("Batch Generation Complete.")

    #CALLBACK
    if on_complete:
        on_complete()

def z_scored_connectome(subject_connectome, reference_connectomes, output_dir, on_complete=None, cancel_checker=None):

    try:
        # Check for cancellation at the start
        if cancel_checker and cancel_checker():
            print("Z-score computation cancelled by user")
            return
        
        # Load the subject matrix

        subject_matrix = np.loadtxt(subject_connectome, delimiter=',')
        
        # Load reference matrices
        ref_matrices = []
        for path in reference_connectomes:
            # Check for cancellation while loading references
            if cancel_checker and cancel_checker():
                print("Z-score computation cancelled by user")
                return
            
            path = path.strip()
            if os.path.exists(path):
                ref_mat = np.loadtxt(path, delimiter=',')
                
                if ref_mat.shape == subject_matrix.shape:
                    ref_matrices.append(ref_mat)
                else:
                    print(f"Skipping {os.path.basename(path)}: Shape {ref_mat.shape} does not match subject.")

        if not ref_matrices:
            print("Error: No valid reference matrices found.")
            return

        # Convert list to 3D array
        ref_stack = np.array(ref_matrices)

        # 4. Calculate element-wise mean and standard deviation
        ref_mean = np.mean(ref_stack, axis=0)
        ref_std = np.std(ref_stack, axis=0)

        # 5. Compute Z-score matrix
        z_matrix = np.zeros_like(subject_matrix)
        mask = ref_std != 0
        z_matrix[mask] = (subject_matrix[mask] - ref_mean[mask]) / ref_std[mask]

        # 6. Formatting the output filename

        subject_basename = os.path.basename(subject_connectome)
        subject_name = os.path.splitext(subject_basename)[0]
        output_name = f"{subject_name}_zscored.csv"
        
        # Create output path
        output_path = os.path.join(output_dir, output_name)
        os.makedirs(output_dir, exist_ok=True)
        np.savetxt(output_path, z_matrix, delimiter=',')

    except Exception as e:
        print(f"Error in Z-score computation: {e}")

    # Callback for the GUI thread
    if on_complete:
        on_complete()

    

def display_connectome(paired_data, on_complete=None):
    
    num_to_display = len(paired_data)
    if num_to_display > 4:
        cols = 4
    else:
        cols = num_to_display
    rows = (num_to_display + cols -1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 5*rows), squeeze=False)
    fig.canvas.manager.set_window_title('Connectome Viewer')

    for i, (csv_path, lut_path) in enumerate(paired_data):
        row, col = i // cols, i % cols
        ax = axes[row, col]
        
        try:
            matrix = np.loadtxt(csv_path, delimiter=',')
            matrix_log = np.log1p(matrix)

            region_names = []
            if os.path.exists(lut_path):
                with open(lut_path, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            region_names.append(parts[1])

            im = ax.imshow(matrix_log, cmap='viridis', interpolation='nearest')

            if len(region_names) == matrix.shape[0]:
                ticks = np.arange(len(region_names))
                ax.set_xticks(ticks)
                ax.set_yticks(ticks)

                ax.set_xticklabels(region_names, rotation=45, ha='right', fontsize=7)
                ax.set_yticklabels(region_names, fontsize=7)

            title = os.path.basename(csv_path).replace("_connectome.csv", "")
            ax.set_title(title, fontsize=10, fontweight='bold')
            
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        except Exception as e:
            ax.text(0.5, 0.5, f"Error:\n{str(e)}", ha='center', va='center', color='red')

    for j in range(i + 1, rows * cols):
        fig.delaxes(axes[j // cols, j % cols])

    plt.tight_layout()
    plt.show()


    if on_complete:
        on_complete()
