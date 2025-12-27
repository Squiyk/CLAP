import customtkinter as ctk
import sys
from pathlib import Path
import threading
from tkinter import filedialog, messagebox
from PIL import Image
import XC_XFM_TOOLBOX
import XC_CONNECTOME_TOOLBOX
import XC_ROI_TOOLBOX
import pygame

class CLAP(ctk.CTk):
    def __init__(self):
        super().__init__()

        pygame.mixer.init()

        self.title("CONNECT LAB ANALYSIS PIPELINE")
        self.geometry("1300x850")

        self.grid_columnconfigure(0, weight=0,minsize=200)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        #### Populating sidebar ####
        self.sidebar_frame = ctk.CTkFrame(self,corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nswe")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        self.header_frame = ctk.CTkFrame(self.sidebar_frame)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.logo_label = ctk.CTkLabel(self.header_frame, text="C.L.A.P. 👏🏻", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.logo_label.bind("<Button-1>", self.play_clapping_sound)

        self.sidebar_btn_1 = ctk.CTkButton(self.sidebar_frame, text="Tools ▼", fg_color="#0078D7", command=self.toggle_tools_menu)
        self.sidebar_btn_1.grid(row=4, column=0, padx=10, pady=10)

        # Tools drawer
        self.tools_drawer = ctk.CTkFrame(self.sidebar_frame)

        self.bt_btn_1 = ctk.CTkButton(self.tools_drawer, text="Home", command=self.setup_home_page)
        self.bt_btn_1.pack(fill="x", padx=10, pady=5)

        self.bt_btn_2 = ctk.CTkButton(self.tools_drawer, text="Registration tools", command=self.setup_registration_tools_page)
        self.bt_btn_2.pack(fill="x", padx=10, pady=5)

        self.bt_btn_3 = ctk.CTkButton(self.tools_drawer, text="Connectome Toolbox", command=self.setup_connectome_toolbox_page)
        self.bt_btn_3.pack(fill="x", padx=10, pady=5)

        self.bt_btn_4 = ctk.CTkButton(self.tools_drawer, text="ROI Parcelation Toolbox", command=self.setup_ROI_toolbox_page)
        self.bt_btn_4.pack(fill="x", padx=10, pady=5)

        #### Populating main pannel ####
        self.main_pannel = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_pannel.grid(row=0, column=1, sticky="nswe")

        self.setup_home_page()

    def toggle_tools_menu(self):
        if self.tools_drawer.winfo_viewable():
            self.tools_drawer.grid_forget()
            self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")
        else:
            self.tools_drawer.grid(row=3, column=0, sticky="ew")
            self.sidebar_btn_1.configure(text="Tools ▲", fg_color="#004E81")

    def clear_main_pannel(self):
        for widget in self.main_pannel.winfo_children():
            widget.destroy()


#### Page Setups ####

    def setup_home_page(self):

        self.clear_main_pannel()

        self.home_page = ctk.CTkFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.home_page.pack(fill="both", expand=True)
        welcome_label = ctk.CTkLabel(self.home_page, text="Welcome to the CONNECT LAB ANALYSIS PIPELINE", font=ctk.CTkFont(size=20, weight="bold"))
        welcome_label.pack(pady=(100,20))
        desc_label = ctk.CTkLabel(self.home_page, text="This application is designed to better organize the scripts produced by the lab and make them more accessible.\nUse the sidebar to navigate through different tools.", font=ctk.CTkFont(size=14))
        desc_label.pack()

        img_path = self.resource_path(Path("complementary_files") / "lab_logo.png")
        pil_image = Image.open(img_path)

        height = 450
        aspect_ratio = pil_image.width / pil_image.height
        width = height * aspect_ratio

        logo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(width,height))
        logo_label = ctk.CTkLabel(self.home_page, image=logo, text="")
        logo_label.pack(pady=(40,20))

        self.tools_drawer.grid_forget()
        self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")

    def setup_registration_tools_page(self):

        # Remove previous page
        self.clear_main_pannel()

        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")

        # Setup new page
        self.registration_tools_page = ctk.CTkScrollableFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.registration_tools_page.pack(fill="both", expand=True)

        self.registration_tools_page.grid_columnconfigure(0, weight=1)


        # Compute new registration, apply and save transforms #

        # Frame for tool
        newreg_frame = ctk.CTkFrame(
            self.registration_tools_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
            )
        newreg_frame.grid(row=0, column=0,pady=20, padx=20, sticky="ew")
        newreg_frame.columnconfigure(1, weight=1)

        # Label for tool
        newreg_label = ctk.CTkLabel(
            newreg_frame,
            text="Compute New Registration (ANTs SyN)",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=("gray10", "gray90")
            )
        newreg_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="w")

        # Fixed image selection
        self.entry_destination_space, btn_dest = self.createrow(newreg_frame, 1, "Fixed image:")
        btn_dest.configure(command=lambda: self.browse_file(self.entry_destination_space))

        # Moving image(s) selection
        self.entry_moving, btn_moving = self.createrow(newreg_frame, 2, "Moving Image:", use_textbox=True)
        btn_moving.configure(command=lambda: self.browse_files(self.entry_moving))

        # Output directory selection
        self.entry_output_reg, out_dir_btn = self.createrow(newreg_frame, 3, "Output Directory:")
        out_dir_btn.configure(command=lambda: self.browse_folder(self.entry_output_reg))

        # Run registration button
        run_new_reg_btn = ctk.CTkButton(
            newreg_frame,
            text="RUN REGISTRATION",
            height=45,
            fg_color="#6A5ACD",
            font=ctk.CTkFont(family="Roboto", size=15, weight="bold"),
            command=lambda: self.start_new_registration_thread()
        )
        run_new_reg_btn.grid(row=4,column=0,columnspan=3, pady=(20,30), padx=20, sticky="ew")


        # Apply existing transforms #

        # Frame for tool
        apply_trans_frame = ctk.CTkFrame(
            self.registration_tools_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        apply_trans_frame.grid(row=1, column=0,pady=20, padx=20, sticky="ew")
        apply_trans_frame.columnconfigure(1, weight=1)

        # Label for tool
        applytrans_label = ctk.CTkLabel(
            apply_trans_frame,
            text="Apply an Existing Transform (ANTs Apply Transform)",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=("gray10", "gray90")
            )
        applytrans_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="w")

        # Moving image(s) selection
        self.entry_moving_apply, mov_image_apply_btn = self.createrow(apply_trans_frame,1,"Moving Image(s)", use_textbox=True)
        mov_image_apply_btn.configure(command=lambda: self.browse_files(self.entry_moving_apply))

        # Transform file selection
        self.entry_transform_file, transform_file_btn = self.createrow(apply_trans_frame,2,"Transform File(s)", use_textbox=True)
        transform_file_btn.configure(command=lambda: self.browse_files(self.entry_transform_file))

        # Reference image selection
        self.entry_reference_apply, ref_image_apply_btn = self.createrow(apply_trans_frame,3,"Reference Image:")
        ref_image_apply_btn.configure(command=lambda: self.browse_file(self.entry_reference_apply))

        # Output directory selection
        self.entry_output_apply, out_dir_apply_btn = self.createrow(apply_trans_frame,4,"Output directory")
        out_dir_apply_btn.configure(command=lambda: self.browse_folder(self.entry_output_apply))

        # Run apply transform button
        run_apply_transform_btn = ctk.CTkButton(
            apply_trans_frame,
            text="APPLY TRANSFORM(S)",
            height=45,
            fg_color="#6A5ACD",
            font=ctk.CTkFont(family="Roboto", size=15, weight="bold"),
            command=lambda: self.start_apply_transform_thread()
        )
        run_apply_transform_btn.grid(row=5,column=0,columnspan=3, pady=(20,30), padx=20, sticky="ew")


    def setup_connectome_toolbox_page(self):

        # Remove previous page
        self.clear_main_pannel()

        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")

        # Setup new page

        self.connectome_toolbox_page = ctk.CTkScrollableFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.connectome_toolbox_page.pack(fill="both", expand=True)

        self.connectome_toolbox_page.grid_columnconfigure(0, weight=1)

        # Generate connectomes from parcellation #

        # Frame for tool
        gen_con_frame = ctk.CTkFrame(
            self.connectome_toolbox_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        gen_con_frame.grid(row=0,column=0,pady=20, padx=20, sticky="ew")
        gen_con_frame.columnconfigure(1, weight=1)

        # Label for tool
        gen_con_label = ctk.CTkLabel(
            gen_con_frame,
            text="Generate connectomes from parcellation",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=("Gray10", "Gray90")
        )
        gen_con_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,10), sticky="w")
        
        # Parcellation selection
        self.entry_mask_img_cntcm, mask_img_cnctm_btn = self.createrow(gen_con_frame,1,"Parcellation:")
        mask_img_cnctm_btn.configure(command=lambda: self.browse_file(self.entry_mask_img_cntcm))

        # Tracts selection
        self.entry_tracks_cnctm, tracks_cnctm_btn = self.createrow(gen_con_frame,2,"Tracts:", use_textbox=True)
        tracks_cnctm_btn.configure(command=lambda: self.get_files_from_folder(self.entry_tracks_cnctm, ".tck"))

        # Select output directory
        self.entry_output_cnctm, output_cnctm_btn = self.createrow(gen_con_frame,3,"Output Directory:")
        output_cnctm_btn.configure(command=lambda: self.browse_folder(self.entry_output_cnctm))

        # Run connectome generation button
        run_cnctm_btn = ctk.CTkButton(
            gen_con_frame,
            text="GENERATE CONNECTOMES",
            height=45,
            fg_color="#6A5ACD",
            font=ctk.CTkFont(family="Roboto", size=15, weight="bold"),
            command=lambda: self.start_connectome_thread()
        )
        run_cnctm_btn.grid(row=4, column=0, columnspan=3, pady=(20,30), padx=20, sticky="ew")


        # Compute z-scored connectome #

        # Frame for tool
        zs_connectome_frame = ctk.CTkScrollableFrame(
            self.connectome_toolbox_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        zs_connectome_frame.grid(row=1, column=0, pady=20, padx=20, sticky="ew")
        zs_connectome_frame.columnconfigure(1, weight=1)

        # Label for tool
        zs_connectome_label = ctk.CTkLabel(
            zs_connectome_frame,
            text="Compute Z-Scored Connectome",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        zs_connectome_frame.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,10), sticky="w")

        # Select subject connectome
        sub_connectome_btn = ctk.CTkButton(self.connectome_toolbox_page, text="Select subject connectome", command=lambda: self.browse_file(self.entry_sub_connectome))
        sub_connectome_btn.grid(row=6, column=0, padx=10, pady=10, sticky="ew")
        self.entry_sub_connectome = ctk.CTkEntry(self.connectome_toolbox_page)
        self.entry_sub_connectome.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        # Select reference connectomes
        ref_connectomes_btn = ctk.CTkButton(self.connectome_toolbox_page, text="Select control connectomes", command=lambda: self.get_files_from_folder(self.entry_ref_connectomes, ".csv"))
        ref_connectomes_btn.grid(row=7, column=0, padx=10, pady=10, sticky="nsew")
        self.entry_ref_connectomes = ctk.CTkTextbox(self.connectome_toolbox_page, height=20)
        self.entry_ref_connectomes.grid(row=7, column=1, padx=10, pady=10, sticky="ew")
        output_zscore_cnctm_btn = ctk.CTkButton(self.connectome_toolbox_page, text="Select Output Directory", command=lambda: self.browse_folder(self.entry_output_zscore_cnctm))
        output_zscore_cnctm_btn.grid(row=8, column=0, padx=10, pady=10, sticky="ew")
        self.entry_output_zscore_cnctm = ctk.CTkEntry(self.connectome_toolbox_page)
        self.entry_output_zscore_cnctm.grid(row=8, column=1, padx=10, pady=10, sticky="ew")
        run_compute_var_vs_ctl_btn = ctk.CTkButton(self.connectome_toolbox_page, text="Compute Z-Score Relative to Controls", height=40, fg_color="#00C448", font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.start_z_scored_connectome_thread())
        run_compute_var_vs_ctl_btn.grid(row=9, column=0, columnspan=2, pady=(10, 30), padx=10, sticky="ew")


        disp_cnctm_label = ctk.CTkLabel(self.connectome_toolbox_page, text="Display Connectome(s)", font=ctk.CTkFont(size=20, weight="bold"))
        disp_cnctm_label.grid(row=10, column=0, pady=20, padx=20, columnspan=2, sticky="w")
        sel_disp_cnctm_btn = ctk.CTkButton(self.connectome_toolbox_page, text="Select connectome(s) to display", command=lambda: self.browse_files(self.entry_disp_cnctm))
        sel_disp_cnctm_btn.grid(row=11,column=0, padx=10, pady=10, sticky="nsew")
        self.entry_disp_cnctm = ctk.CTkTextbox(self.connectome_toolbox_page, height=20)
        self.entry_disp_cnctm.grid(row=11, column=1, padx=10, pady=10, sticky="ew")
        sel_disp_lut_btn = ctk.CTkButton(self.connectome_toolbox_page, text="Select LUT file(s)", command=lambda:self.browse_files(self.entry_disp_lut))
        sel_disp_lut_btn.grid(row=12, column=0, padx=10, pady=10, sticky="nsew")
        self.entry_disp_lut = ctk.CTkTextbox(self.connectome_toolbox_page, height=20)
        self.entry_disp_lut .grid(row=12, column=1, padx=10, pady=10, sticky="ew")
        run_disp_cnctm_btn = ctk.CTkButton(self.connectome_toolbox_page, text="Display Connectome(s)", height=40, fg_color="#00C448", font=ctk.CTkFont(size=14, weight="bold"))
        run_disp_cnctm_btn.grid(row=13, column=0, columnspan=2, pady=(10, 30), padx=10, sticky="ew")

    def setup_ROI_toolbox_page(self):
        self.clear_main_pannel()
        self.ROI_toolbox_page = ctk.CTkFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.ROI_toolbox_page.pack(fill="both", expand=True)
        SEEG_ROI_Mask_tool_label = ctk.CTkLabel(self.ROI_toolbox_page, text="SEEG ROI Mask Generation Tool", font=ctk.CTkFont(size=20, weight="bold"))
        self.ROI_toolbox_page.columnconfigure(1, weight=1)
        self.tools_drawer.grid_forget()
        self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")
        
        SEEG_ROI_Mask_tool_label.grid(row=0, column=0, pady=20, padx=20, columnspan=2, sticky="w")
        sel_ref_mask_img_btn = ctk.CTkButton(self.ROI_toolbox_page, text="Select Reference Mask Image", command=lambda: self.browse_file(self.entry_ref_mask_img))
        sel_ref_mask_img_btn.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.entry_ref_mask_img = ctk.CTkEntry(self.ROI_toolbox_page)
        self.entry_ref_mask_img.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        sel_seeg_coords_btn = ctk.CTkButton(self.ROI_toolbox_page, text="Select SEEG Coordinates File", command=lambda: self.browse_file(self.entry_seeg_coords))
        sel_seeg_coords_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self.entry_seeg_coords = ctk.CTkEntry(self.ROI_toolbox_page)
        self.entry_seeg_coords.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        out_roi_mask_dir_btn = ctk.CTkButton(self.ROI_toolbox_page, text="Select Output ROI Mask Directory", command=lambda: self.browse_folder(self.entry_output_roi_mask_dir))
        out_roi_mask_dir_btn.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.entry_output_roi_mask_dir = ctk.CTkEntry(self.ROI_toolbox_page)
        self.entry_output_roi_mask_dir.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.sel_compute_mode_segbtn = ctk.CTkSegmentedButton(self.ROI_toolbox_page, values=["Monopolar", "Bipolar"], fg_color="#515151", unselected_color="#515151",selected_color="#0078D7")
        self.sel_compute_mode_segbtn.set("Monopolar")
        self.sel_compute_mode_segbtn.grid(row=1, column=2, sticky="ew", padx=10, pady=10)

        radius_container = ctk.CTkFrame(self.ROI_toolbox_page, fg_color="transparent")
        radius_container.grid(row=2, column=2, padx=10, pady=10, rowspan=2, sticky="ew")
        radius_container_label = ctk.CTkLabel(radius_container, text="Select sphere radius :", font=ctk.CTkFont(size=12))
        radius_container_label.pack(pady=(0,2), anchor="w")
        radius_input_row = ctk.CTkFrame(radius_container, fg_color="transparent")
        radius_input_row.pack(fill="x")
        self.sel_compute_radius = ctk.CTkEntry(radius_input_row)
        self.sel_compute_radius.pack(side="left", fill="x",expand=True)
        self.sel_compute_radius.insert(0, "2")
        sel_radius_unit_label = ctk.CTkLabel(radius_input_row, text="(mm)", text_color="#929292")
        sel_radius_unit_label.pack(side="left", padx=(5,0))

        run_seeg_roi_mask_tool_btn = ctk.CTkButton(self.ROI_toolbox_page, text="Generate SEEG ROI Mask", height=40, fg_color="#00C448", font=ctk.CTkFont(size=14, weight="bold"), command=lambda: self.start_seeg_roi_mask_thread())
        run_seeg_roi_mask_tool_btn.grid(row=4, column=0, columnspan=2, pady=(10, 30), padx=10, sticky="ew")
        

### HELPER FUNCTIONS ###

# UI design functions

    def createrow(self, parent, row_idx, label_text, start_col=0, entry_span=1, use_textbox=False):
        lbl = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(family="Roboto", size=14),
            text_color=("gray30", "gray80")
        )
        lbl.grid(row=row_idx, column=start_col, padx=(20,10),pady=10, sticky="w")

        if use_textbox:
            entry = ctk.CTkTextbox(
                parent,
                height=35,
                border_color=("#D0D0D0", "#505050"), 
                fg_color=("white", "#343638"),
                text_color=("black", "white"),
                border_width=2
            )
        else:
            entry = ctk.CTkEntry(
                parent,
                height=35,
                border_color=("#D0D0D0", "#505050"), 
                fg_color=("white", "#343638"),
                text_color=("black", "white"),
                border_width=2
            )
        entry.grid(row=row_idx,column=start_col+1, columnspan=entry_span, padx=10, pady=10, sticky="ew")

        btn_col = start_col+ 1 + entry_span

        btn = ctk.CTkButton(
            parent,
            text="...",
            width=40,
            height=35,
            fg_color=("#F0F0F0", "#3A3A3A"),
            text_color=("black", "white"),
            hover_color=("#D9D9D9", "#505050")
        )
        btn.grid(row = row_idx, column=btn_col, padx=(0,20),pady=10)
        
        return entry, btn



# Critical functionality
    def resource_path(self, relative_path):
            try:
                base_path = Path(sys._MEIPASS)
            except Exception:
                base_path = Path(__file__).parent

            return base_path / relative_path

    def play_clapping_sound(self, event=None):
            try :
                sound_path = self.resource_path(Path("complementary_files") / "CriticalSupportFIle.mp3")
                pygame.mixer.music.load(str(sound_path))
                pygame.mixer.music.play()
            except Exception as e:
                 print(f"You removed critical functionality :( Error: {e}")


# File/folder browsing helpers #
    def browse_file(self, entry_widget):
        path = filedialog.askopenfilename()
        if path:
            entry_widget.delete(0, ctk.END)
            entry_widget.insert(0, path)

    def browse_files(self, textbox_widget):
            file_paths = filedialog.askopenfilenames()
            if file_paths:
                joined_paths = "\n".join(file_paths)
                textbox_widget.delete("0.0", "end")
                textbox_widget.insert("0.0", joined_paths)

                num_files = len(file_paths)
                new_height = (num_files * 20)+10

                final_height = min(200, new_height)

                textbox_widget.configure(height=final_height)

    def get_files_from_folder(self, textbox_widget, extension):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return

        folder = Path(folder_path)
        files_paths = [str(p) for p in folder.rglob(f"*{extension}")]

        if files_paths:
            joined_paths = "\n".join(files_paths)
            textbox_widget.delete("0.0", "end")
            textbox_widget.insert("0.0", joined_paths)

            num_files = len(files_paths)
            new_height = (num_files * 20) + 10
            final_height = min(200, new_height)

            textbox_widget.configure(height=final_height)

    def browse_folder(self, entry_widget):
        path = filedialog.askdirectory()
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

## Registration threading ##

# New registration thread starter
    def start_new_registration_thread(self):
        
        out = self.entry_output_reg.get().strip()
        fixed = self.entry_destination_space.get().strip()
        
        raw_inputs = self.entry_moving.get("0.0", "end")
        moving_list = [line.strip() for line in raw_inputs.split("\n") if line.strip()]

        if not out or not fixed or not moving_list:
            messagebox.showerror("Error", "Please provide all required inputs for registration.")
            return
        task = threading.Thread(target=XC_XFM_TOOLBOX.new_xfm, args=(out, fixed, moving_list, self.on_registration_complete))
        task.start()

    def on_registration_complete(self):
        self.after(0,self.show_new_registration_complete_message)

    def show_new_registration_complete_message(self):
        messagebox.showinfo("Success", "Registration Complete")

# Apply transform thread starter

    def start_apply_transform_thread(self):
            out_dir = self.entry_output_apply.get().strip()
            reference = self.entry_reference_apply.get().strip()

            raw_moving = self.entry_moving_apply.get("0.0", "end")
            moving_list = [line.strip() for line in raw_moving.split("\n") if line.strip()]

            raw_transforms = self.entry_transform_file.get("0.0", "end")
            transform_list = [line.strip() for line in raw_transforms.split("\n") if line.strip()]

            if not out_dir or not reference or not moving_list or not transform_list:
                messagebox.showerror("Input Error", "Please provide Reference, Output, at least one Moving Image, and at least one Transform.")
                return

            task = threading.Thread(target=XC_XFM_TOOLBOX.apply_existing_xfm, args=(out_dir, transform_list, moving_list, reference, self.on_apply_complete))
            task.start()

    def on_apply_transform_complete(self):
        self.after(0,self.show_apply_transform_complete_message)
        
    def show_apply_transform_complete_message(self):
        messagebox.showinfo("Success", "Transform Application Complete")

## Connectome threading ##

# Generate connectome thread starter

    def start_connectome_thread(self):
        mask_image = self.entry_mask_img_cntcm.get().strip()

        raw_tracks = self.entry_tracks_cnctm.get("0.0", "end")
        tracks_list = [line.strip() for line in raw_tracks.split("\n") if line.strip()]

        output_dir = self.entry_output_cnctm.get().strip()

        if not mask_image or not tracks_list:
            messagebox.showerror("Input Error", "Please provide Mask Image and at least one Track file.")
            return

        task = threading.Thread(target=XC_CONNECTOME_TOOLBOX.gen_connectome, args=(mask_image, tracks_list, output_dir, self.on_connectome_complete))
        task.start()

    def on_connectome_complete(self):
        self.after(0,self.show_connectome_complete_message)

    def show_connectome_complete_message(self):
        messagebox.showinfo("Success", "Connectome Generation Complete")

# Generate z-scored connectome thread starter
    def start_z_scored_connectome_thread(self):
        subject_connectome = self.entry_sub_connectome.get().strip()
        raw_ref_connectomes = self.entry_ref_connectomes.get("0.0", "end")
        ref_connectomes_list = [line.strip() for line in raw_ref_connectomes.split("\n") if line.strip()]
        output_dir = self.entry_output_zscore_cnctm.get().strip()

        if not subject_connectome or not ref_connectomes_list or not output_dir:
            messagebox.showerror("Input Error", "Please provide Subject Connectome, Reference Connectomes, and Output Directory.")
            return

        task = threading.Thread(target=XC_CONNECTOME_TOOLBOX.z_scored_connectome, args=(subject_connectome, ref_connectomes_list, output_dir, self.on_z_score_complete))
        task.start()

    def on_z_score_complete(self):
        self.after(0,self.show_z_score_complete_message)

    def show_z_score_complete_message(self):
        messagebox.showinfo("Success", "Z-Score Computation Complete")

# Display connectome thread starter
    def start_display_connectome_thread(self):
        raw_cnctms = self.entry_disp_cnctm.get("0.0", "end")
        cnctms_list = [line.strip() for line in raw_cnctms.split("\n") if line.strip()]
        raw_luts = self.entry_disp_lut.get("0.0", "end")
        luts_list = [line.strip() for line in raw_luts.split("\n") if line.strip()]

        if not cnctms_list or not luts_list:
            messagebox.showerror("Input Error", "Please provide at least one Connectome and one LUT file.")
            return
        
        lut_map = {}
        for lut in luts_list:
            base = Path(lut).stem.replace("_LUT", "")
            lut_map[base] = lut

        paired_data = []
        for cnctm in cnctms_list:
            name = Path(cnctm).stem.replace("_connectome", "")
            if name in lut_map:
                paired_data.append((cnctm, lut_map[name]))
            else:
                messagebox.showwarning("Warning", f"No matching LUT found for connectome: {name}")
        
        if not paired_data:
            messagebox.showerror("Input Error", "No valid Connectome-LUT pairs found.")
            return

        task = threading.Thread(target=XC_CONNECTOME_TOOLBOX.display_connectome, args=(paired_data, self.on_display_complete))
        task.start()
    
    def on_display_complete(self):
        self.after(0,self.show_display_complete_message)

    def show_display_complete_message(self):
        messagebox.showinfo("Success", "Connectome Display Complete")

## ROI Toolbox threading ##
    def start_seeg_roi_mask_thread(self):
        ref_mask_img = self.entry_ref_mask_img.get().strip()
        seeg_coords_file = self.entry_seeg_coords.get().strip()
        output_dir = self.entry_output_roi_mask_dir.get().strip()
        raw_rad = self.sel_compute_radius.get()
        raw_mode = self.sel_compute_mode_segbtn.get()

        try:
            sel_rad = float(raw_rad)
        except ValueError:
            messagebox.showerror("Input Error","Radius mus be a valid number")
            return    
        
        is_bipolar_mode = (raw_mode == "Bipolar") 

        if not ref_mask_img or not seeg_coords_file or not output_dir:
            messagebox.showerror("Input Error", "Please provide Reference Mask Image, SEEG Coordinates File, and Output Directory.")
            return

        task = threading.Thread(target=XC_ROI_TOOLBOX.generate_seeg_roi_masks, args=(ref_mask_img, seeg_coords_file, output_dir, sel_rad, is_bipolar_mode, self.on_seeg_roi_mask_complete))
        task.start()

    def on_seeg_roi_mask_complete(self):
        self.after(0,self.show_seeg_roi_mask_complete_message)

    def show_seeg_roi_mask_complete_message(self):
        messagebox.showinfo("Success", "SEEG ROI Mask Generation Complete")

# MAIN LOOP #        
if __name__ == "__main__":
    app = CLAP()
    app.mainloop()