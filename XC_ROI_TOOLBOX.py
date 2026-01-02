from pathlib import Path
import nibabel as nib
import numpy as np
import matplotlib.cm as cm
import re

def generate_seeg_roi_masks(ref_mask_img, seeg_coords_file, output_dir, sel_rad, is_bipolar_mode, on_complete=None, cancel_checker=None):

    ref_path = Path(ref_mask_img)
    coords_path = Path(seeg_coords_file)
    output_dir_path = Path(output_dir)
    Radius_mm = sel_rad

    success = False
    try:
        # Check for cancellation at the start
        if cancel_checker and cancel_checker():
            print("SEEG ROI mask generation cancelled by user")
            if on_complete:
                on_complete(success=False)
            return
        
        img = nib.load(ref_path)
        affine = img.affine
        inv_affine = np.linalg.inv(affine)
        data_shape = img.shape
        zooms = img.header.get_zooms()[:3]

        mask_data = np.zeros(data_shape, dtype=np.int16)
        clean_base = clean_subject_name(ref_path)

        raw_contacts = []
        with coords_path.open('r') as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()

                if len(parts) >= 4:
                    try:
                        x = float(parts[0])
                        y = float(parts[1])
                        z = float(parts[2])
                        name = parts[3]

                        raw_contacts.append({'name': name, 'coords': np.array([x, y, z])})
                    except ValueError:
                        print(f"Invalid line in coordinates file: {line}")

        final_contacts = []

        if is_bipolar_mode:
            for i in range(len(raw_contacts)-1):
                c1 = raw_contacts[i]
                c2 =raw_contacts[i+1]

                match1 = re.search(r"^(.*?)(\d+)$", c1['name'])
                match2 = re.search(r"^(.*?)(\d+)$", c2['name'])

                if match1 and match2 and match1.group(1) == match2.group(1):
                    idx1 = int(match1.group(2))
                    idx2 = int(match2.group(2))

                    if abs(idx2-idx1) == 1:
                        mid_coords = (c1['coords'] + c2['coords']) / 2
                        new_name = f"{c1['name']}-{c2['name']}"

                        final_contacts.append({'name': new_name, 'coords': mid_coords})

        else:
            final_contacts = raw_contacts


        lut_entries = []
        lut_entries.append(f"0 Background 0 0 0 0")

        for i, contact in enumerate(final_contacts):
            # Check for cancellation while processing contacts
            if cancel_checker and cancel_checker():
                print("SEEG ROI mask generation cancelled by user")
                if on_complete:
                    on_complete(success=False)
                return
            
            contact_id = i + 1
            world_coords = np.array(contact['coords'])

            voxel_coords = nib.affines.apply_affine(inv_affine, world_coords)
            center_vox = np.round(voxel_coords).astype(int)

            rad_vox = np.ceil(Radius_mm / np.min(zooms)).astype(int)

            x_min = max(0, center_vox[0] - rad_vox)
            x_max = min(data_shape[0], center_vox[0] +rad_vox +1)
            y_min = max(0, center_vox[1] - rad_vox)
            y_max = min(data_shape[1], center_vox[1] +rad_vox +1)
            z_min = max(0, center_vox[2] - rad_vox)
            z_max = min(data_shape[2], center_vox[2] +rad_vox +1)

            for x in range(x_min, x_max):
                for y in range(y_min, y_max):
                    for z in range(z_min, z_max):
                        current_vox = np.array([x, y, z])
                        current_world = nib.affines.apply_affine(affine, current_vox)
                        dist = np.linalg.norm(current_world - world_coords)
                        if dist <= Radius_mm:
                            mask_data[x, y, z] = contact_id
            color = cm.nipy_spectral(float(i) / len(final_contacts))
            r, g, b = int(color[0]*255), int(color[1]*255), int(color[2]*255)
            lut_entries.append(f"{contact_id} {contact['name']} {r} {g} {b} 0")

        output_dir_path.mkdir(parents=True, exist_ok=True)

        if is_bipolar_mode:
            suffix = "BIPOLAR"
        else:
            suffix = "MONOPOLAR"

        nifti_name = f"{clean_base}_SEEG_{suffix}_parcellation.nii.gz"
        nifti_path = output_dir_path / nifti_name
        new_img = nib.Nifti1Image(mask_data, affine, img.header)
        nib.save(new_img, nifti_path)


        lut_name = f"{clean_base}_{suffix}_LUT.txt"
        lut_path = output_dir_path / lut_name

        with lut_path.open('w') as f_lut:
            f_lut.write(f"# LUT for SEEG ROI parcellation ({clean_base})\n")
            f_lut.write(f"# ID Name R G B A\n")
            for entry in lut_entries:
                parts = entry.split()
                f_lut.write(f"{parts[0]:>4} {parts[1]:<25} {parts[2]:>3} {parts[3]:>3} {parts[4]:>3} {parts[5]:>3}\n")
        
        success = True

    except Exception as e:
        print(f"Critical error : {e}")

    if on_complete:
        on_complete(success=success)


def clean_subject_name(filename):
    path_obj = Path(filename)
    base_name = path_obj.name

    if "_" in base_name:
        return base_name.split("_")[0]
    
    if base_name.endswith(".nii.gz"):
        return base_name[:-7]
    
    return path_obj.stem