import customtkinter as ctk
import sys
from pathlib import Path
import threading
from tkinter import filedialog, messagebox
from PIL import Image
from datetime import datetime
import XC_XFM_TOOLBOX
import XC_CONNECTOME_TOOLBOX
import XC_ROI_TOOLBOX
import pygame
from clap_settings import SettingsManager
from clap_task_logger import TaskLogger

class CLAP(ctk.CTk):
    def __init__(self):
        super().__init__()

        pygame.mixer.init()
        
        # Initialize settings and task logger
        self.settings_manager = SettingsManager()
        self.task_logger = TaskLogger()
        self.current_task_thread = None
        self.current_task_id = None
        self.cancel_task_flag = False

        self.title("CONNECT LAB ANALYSIS PIPELINE")
        self.geometry("1300x850")

        # Apply saved appearance settings
        appearance_mode = self.settings_manager.get("appearance_mode", "System")
        ctk.set_appearance_mode(appearance_mode)
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=0,minsize=200)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar setup
        self.sidebar_frame = ctk.CTkFrame(self,corner_radius=0, fg_color="transparent")
        self.sidebar_frame.grid(row=0, column=0, sticky="nswe")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        #  Sidebar title card
        sidebar_title_card = ctk.CTkFrame(
            self.sidebar_frame, corner_radius=10,
            fg_color=("white", "#2B2B2B"),
            border_width=1,
            border_color=("#E0E0E0", "#404040")
            )
        sidebar_title_card.grid(row=0, column=0, sticky="nswe", padx=(20,0), pady=20)
        sidebar_title_card.grid_columnconfigure(0, weight=1, minsize=200)

        logo_label = ctk.CTkLabel(sidebar_title_card, text="C.L.A.P. 👏🏻", font=ctk.CTkFont(size=20, weight="bold"),corner_radius=0)
        logo_label.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        logo_label.bind("<Button-1>", self.play_clapping_sound)

        # Sidebar button card
        sidebar_button_card = ctk.CTkFrame(
            self.sidebar_frame, corner_radius=10,
            fg_color=("white", "#2B2B2B"),
            border_width=1,
            border_color=("#E0E0E0", "#404040")
            )
        sidebar_button_card.grid(row=1, column=0, sticky="nswe", padx=(20,0), pady=(0,20))
        sidebar_button_card.grid_columnconfigure(0, weight=1)
        sidebar_button_card.grid_rowconfigure(0, weight=1)

        # Sidebar buttons
        self.sidebar_btn_1 = ctk.CTkButton(sidebar_button_card, text="Tools ▼", fg_color="#0078D7", command=self.toggle_tools_menu)
        self.sidebar_btn_1.grid(row=1, column=0, padx=5, pady=20)

        # Tools drawer
        self.tools_drawer = ctk.CTkFrame(sidebar_button_card, fg_color="transparent")

        self.bt_btn_1 = ctk.CTkButton(self.tools_drawer, text="Home", command=self.setup_home_page)
        self.bt_btn_1.pack(fill="x", padx=10, pady=5)

        self.bt_btn_2 = ctk.CTkButton(self.tools_drawer, text="Registration tools", command=self.setup_registration_tools_page)
        self.bt_btn_2.pack(fill="x", padx=10, pady=5)

        self.bt_btn_3 = ctk.CTkButton(self.tools_drawer, text="Connectome Toolbox", command=self.setup_connectome_toolbox_page)
        self.bt_btn_3.pack(fill="x", padx=10, pady=5)

        self.bt_btn_4 = ctk.CTkButton(self.tools_drawer, text="ROI Parcelation Toolbox", command=self.setup_ROI_toolbox_page)
        self.bt_btn_4.pack(fill="x", padx=10, pady=5)
        
        # Additional buttons (Settings and History)
        self.sidebar_btn_2 = ctk.CTkButton(sidebar_button_card, text="Settings ⚙️", fg_color="#0078D7", command=self.setup_settings_page)
        self.sidebar_btn_2.grid(row=2, column=0, padx=5, pady=10)
        
        self.sidebar_btn_3 = ctk.CTkButton(sidebar_button_card, text="History 📋", fg_color="#0078D7", command=self.setup_history_page)
        self.sidebar_btn_3.grid(row=3, column=0, padx=5, pady=10)
        
        # Task status frame (appears when task is running)
        self.task_status_frame = ctk.CTkFrame(
            sidebar_button_card,
            fg_color=("white", "#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        
        self.task_status_label = ctk.CTkLabel(
            self.task_status_frame,
            text="Task Running...",
            font=ctk.CTkFont(family="Proxima Nova", size=12, weight="bold"),
            text_color=("gray10", "gray90")
        )
        self.task_status_label.pack(padx=10, pady=(10, 5))
        
        self.task_progress_bar = ctk.CTkProgressBar(
            self.task_status_frame,
            mode="indeterminate"
        )
        self.task_progress_bar.pack(padx=10, pady=5, fill="x")
        
        self.cancel_task_btn = ctk.CTkButton(
            self.task_status_frame,
            text="Cancel Task",
            fg_color="#DC3545",
            hover_color="#C82333",
            command=self.cancel_current_task
        )
        self.cancel_task_btn.pack(padx=10, pady=(5, 10), fill="x")

        #### Populating main pannel ####
        self.main_pannel = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_pannel.grid(row=0, column=1, sticky="nswe")

        # Restore last page and menu state
        self._restore_ui_state()

    def toggle_tools_menu(self):
        if self.tools_drawer.winfo_viewable():
            self.tools_drawer.grid_forget()
            self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")
            self.settings_manager.set("tools_menu_expanded", False)
        else:
            self.tools_drawer.grid(row=0, column=0, sticky="sew")
            self.sidebar_btn_1.configure(text="Tools ▲", fg_color="#004E81")
            self.settings_manager.set("tools_menu_expanded", True)
    
    def _restore_ui_state(self):
        """Restore UI state from settings"""
        # Restore menu expansion state
        if self.settings_manager.get("tools_menu_expanded", False):
            self.tools_drawer.grid(row=0, column=0, sticky="sew")
            self.sidebar_btn_1.configure(text="Tools ▲", fg_color="#004E81")
        
        # Restore last page
        last_page = self.settings_manager.get("last_page", "home")
        page_methods = {
            "home": self.setup_home_page,
            "registration": self.setup_registration_tools_page,
            "connectome": self.setup_connectome_toolbox_page,
            "roi": self.setup_ROI_toolbox_page,
            "settings": self.setup_settings_page,
            "history": self.setup_history_page
        }
        page_method = page_methods.get(last_page, self.setup_home_page)
        page_method()
    
    def _save_current_page(self, page_name):
        """Save current page to settings"""
        self.settings_manager.set("last_page", page_name)
    
    def _show_task_status(self, task_name):
        """Show task status frame and start progress bar"""
        self.task_status_label.configure(text=f"Running: {task_name}")
        self.task_status_frame.grid(row=4, column=0, padx=5, pady=10, sticky="ew")
        self.task_progress_bar.start()
    
    def _hide_task_status(self):
        """Hide task status frame and stop progress bar"""
        self.task_progress_bar.stop()
        self.task_status_frame.grid_forget()
    
    def cancel_current_task(self):
        """Cancel the currently running task
        
        Note: This marks the task as cancelled in the UI and log, but the actual
        background thread will continue to completion since the task execution
        functions don't currently check for cancellation flags. To fully support
        cancellation, the underlying task functions would need to be modified to
        periodically check a cancellation flag.
        """
        if self.current_task_id is not None:
            self.cancel_task_flag = True
            self.task_logger.complete_task(self.current_task_id, "interrupted", "User cancelled")
            self.current_task_id = None
            self.current_task_thread = None
            self._hide_task_status()
            messagebox.showinfo("Task Cancelled", "The current task has been cancelled.")

    def clear_main_pannel(self):
        for widget in self.main_pannel.winfo_children():
            widget.destroy()


#### Page Setups ####

    def setup_home_page(self):

        self.clear_main_pannel()
        self._save_current_page("home")

        self.home_page = ctk.CTkFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.home_page.pack(fill="both", expand=True)

        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")

        # Create Home page card
        home_card = ctk.CTkFrame(
            self.home_page,
            corner_radius=10,
            fg_color=("white", "#2B2B2B"),
            border_width=1,
            border_color=("#E0E0E0", "#404040")
            )
        home_card.pack(padx=20, pady=20, fill="both", expand=True)

        welcome_label = ctk.CTkLabel(home_card, text="Welcome to the CONNECT LAB ANALYSIS PIPELINE", font=ctk.CTkFont(size=20, weight="bold"))
        welcome_label.pack(pady=(100,20))
        desc_label = ctk.CTkLabel(home_card, text="This application is designed to better organize the scripts produced by the lab and make them more accessible.\nUse the sidebar to navigate through different tools.", font=ctk.CTkFont(size=14))
        desc_label.pack()

        img_path = self.resource_path(Path("complementary_files") / "lab_logo.png")
        pil_image = Image.open(img_path)

        height = 450
        aspect_ratio = pil_image.width / pil_image.height
        width = height * aspect_ratio

        logo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(width,height))
        logo_label = ctk.CTkLabel(home_card, image=logo, text="")
        logo_label.pack(pady=(40,20))


    def setup_registration_tools_page(self):

        # Remove previous page
        self.clear_main_pannel()
        self._save_current_page("registration")

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
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
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
            font=ctk.CTkFont(family="Proxima Nova", size=15, weight="bold"),
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
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
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
            font=ctk.CTkFont(family="Proxima Nova", size=15, weight="bold"),
            command=lambda: self.start_apply_transform_thread()
        )
        run_apply_transform_btn.grid(row=5,column=0,columnspan=3, pady=(20,30), padx=20, sticky="ew")


    def setup_connectome_toolbox_page(self):

        # Remove previous page
        self.clear_main_pannel()
        self._save_current_page("connectome")

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
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("Gray10", "Gray90")
        )
        gen_con_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,10), sticky="w")
        
        # Parcellation selection
        self.entry_mask_img_cntcm, mask_img_cnctm_btn = self.createrow(gen_con_frame,1,"Parcellation:")
        mask_img_cnctm_btn.configure(command=lambda: self.browse_file(self.entry_mask_img_cntcm))

        # Tracts selection
        self.entry_tracks_cnctm, tracks_cnctm_btn = self.createrow(gen_con_frame,2,"Tracts:", use_textbox=True)
        tracks_cnctm_btn.configure(command=lambda: self.get_files_from_folder(self.entry_tracks_cnctm, ".tck"))

        # Tract weights file selection
        self.entry_tracks_cnctm_weights, tracks_cnctm_weights_btn = self.createrow(gen_con_frame,3,"Tract Weights Files (optional):", use_textbox=True)
        tracks_cnctm_weights_btn.configure(command=lambda: self.get_files_from_folder(self.entry_tracks_cnctm_weights, ".csv"))

        # Select output directory
        self.entry_output_cnctm, output_cnctm_btn = self.createrow(gen_con_frame,4,"Output Directory:")
        output_cnctm_btn.configure(command=lambda: self.browse_folder(self.entry_output_cnctm))

        # Run connectome generation button
        run_cnctm_btn = ctk.CTkButton(
            gen_con_frame,
            text="GENERATE CONNECTOMES",
            height=45,
            fg_color="#6A5ACD",
            font=ctk.CTkFont(family="Proxima Nova", size=15, weight="bold"),
            command=lambda: self.start_connectome_thread()
        )
        run_cnctm_btn.grid(row=5, column=0, columnspan=3, pady=(20,30), padx=20, sticky="ew")


        # Compute z-scored connectome #

        # Frame for tool
        zs_connectome_frame = ctk.CTkFrame(
            self.connectome_toolbox_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        zs_connectome_frame.grid(row=1,column=0,pady=20, padx=20, sticky="ew")
        zs_connectome_frame.columnconfigure(1, weight=1)

        # Label for tool
        zs_connectome_label = ctk.CTkLabel(
            zs_connectome_frame,
            text="Compute Z-Scored Connectome",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        zs_connectome_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,10), sticky="w")

        # Select subject connectome
        self.entry_sub_connectome, sub_connectome_btn = self.createrow(zs_connectome_frame,2,"Subject Connectome:")
        sub_connectome_btn.configure(command=lambda: self.browse_file(self.entry_sub_connectome))

        # Select reference connectomes
        self.entry_ref_connectomes, ref_connectomes_btn = self.createrow(zs_connectome_frame,3,"Reference connectomes", use_textbox=True)
        ref_connectomes_btn.configure(command=lambda: self.get_files_from_folder(self.entry_ref_connectomes, ".csv"))

        # Select output directory
        self.entry_output_zscore_cnctm, output_zscore_cnctm_btn = self.createrow(zs_connectome_frame,4,"Output Directory:")
        output_zscore_cnctm_btn.configure(command=lambda: self.browse_folder(self.entry_output_zscore_cnctm))

        # Run Z-scoring of connectome
        run_compute_var_vs_ctl_btn = ctk.CTkButton(
            zs_connectome_frame,
            text="Z-SCORE CONNECTOME",
            height=45,
            fg_color="#6A5ACD",
            font=ctk.CTkFont(family="Proxima Nova", size=15, weight="bold"),
            command=lambda: self.start_z_scored_connectome_thread()
        )
        run_compute_var_vs_ctl_btn.grid(row=5, column=0, columnspan=3, pady=(20,30), padx=20, sticky="ew")


        # Display select connectomes #

        # Frame for tool
        disp_cnctm_frame = ctk.CTkFrame(
            self.connectome_toolbox_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        disp_cnctm_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        disp_cnctm_frame.columnconfigure(1, weight=1)

        # Label for tool
        disp_cnctm_label = ctk.CTkLabel(
            disp_cnctm_frame,
            text="Display Connectomes",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
            )
        disp_cnctm_label.grid(row=0, column=0,columnspan=3, padx=20, pady=(20,10), sticky="w")

        # Select connectomes to be displayed
        self.entry_disp_cnctm, sel_disp_cnctm_btn = self.createrow(disp_cnctm_frame,1,"Connectome(s):", use_textbox=True)
        sel_disp_cnctm_btn.configure(command=lambda: self.browse_files(self.entry_disp_cnctm))

        # Select LUTs for axis annotation
        self.entry_disp_lut, sel_disp_lut_btn = self.createrow(disp_cnctm_frame,2,"LUT file(s):", use_textbox=True)
        sel_disp_lut_btn.configure(command=lambda: self.browse_files(self.entry_disp_lut))

        # Run connectome display button
        run_disp_cnctm_btn = ctk.CTkButton(
        disp_cnctm_frame,
        text="DISPLAY CONNECTOMES",
        height=45,
        fg_color="#6A5ACD",
        font=ctk.CTkFont(family="Proxima Nova", size=15, weight="bold"),
        command=lambda: self.start_display_connectome_thread()
        )
        run_disp_cnctm_btn.grid(row=3, column=0, columnspan=3, pady=(20,30), padx=20, sticky="ew")

    def setup_ROI_toolbox_page(self):

        # Remove previous page
        self.clear_main_pannel()
        self._save_current_page("roi")

        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")

        # Setup new page
        self.ROI_toolbox_page = ctk.CTkScrollableFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.ROI_toolbox_page.pack(fill="both", expand=True)

        self.ROI_toolbox_page.columnconfigure(0, weight=1)

        #  SEEG ROI Mask Generation Tool #

        # Frame for tool
        SEEG_ROI_Mask_tool_frame = ctk.CTkFrame(
            self.ROI_toolbox_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        SEEG_ROI_Mask_tool_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        SEEG_ROI_Mask_tool_frame.columnconfigure(1, weight=1)

        # Label for tool
        SEEG_ROI_Mask_tool_label = ctk.CTkLabel(
            SEEG_ROI_Mask_tool_frame,
            text="SEEG ROI Mask Generation Tool",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        SEEG_ROI_Mask_tool_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,10), sticky="w")

        # Select input image
        self.entry_ref_mask_img, sel_ref_mask_img_btn = self.createrow(SEEG_ROI_Mask_tool_frame,1,"Reference Mask Image:")
        sel_ref_mask_img_btn.configure(command=lambda: self.browse_file(self.entry_ref_mask_img))

        # Select SEEG coordinates file
        self.entry_seeg_coords, sel_seeg_coords_btn = self.createrow(SEEG_ROI_Mask_tool_frame,2,"SEEG Coordinates File:")
        sel_seeg_coords_btn.configure(command=lambda: self.browse_file(self.entry_seeg_coords))

        # Select output ROI mask directory
        self.entry_output_roi_mask_dir, out_roi_mask_dir_btn = self.createrow(SEEG_ROI_Mask_tool_frame,3,"Output ROI Mask Directory:")
        out_roi_mask_dir_btn.configure(command=lambda: self.browse_folder(self.entry_output_roi_mask_dir))


        # Radius and mode selection

        # Create frame for radius and mode selection
        radius_mode_frame = ctk.CTkFrame(SEEG_ROI_Mask_tool_frame, fg_color="transparent")
        radius_mode_frame.grid(row=4, column=0, columnspan=3, padx=20, pady=(10,20), sticky="ew")

        #Radius selection
        lbl_rad = ctk.CTkLabel(
            radius_mode_frame,
            text="Sphere Radius:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        lbl_rad.pack(side="left", padx=(0,10))

        self.sel_compute_radius = ctk.CTkEntry(
            radius_mode_frame,
            width=60,
            justify="center",
            fg_color=("white", "#343638")
        )
        self.sel_compute_radius.insert(0, "2")
        self.sel_compute_radius.pack(side="left")

        lbl_mm = ctk.CTkLabel(
            radius_mode_frame,
            text="(mm)",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30","gray80")
        )
        lbl_mm.pack(side="left", padx=(5,0))


        self.sel_compute_mode_segbtn = ctk.CTkSegmentedButton(
            radius_mode_frame,
            values=["Monopolar", "Bipolar"],
            fg_color=("gray70", "gray30"),
            unselected_color=("gray70", "gray30"),
            selected_hover_color="#005A9E",
            selected_color="#0078D7"
        )
        self.sel_compute_mode_segbtn.pack(side="right")
        self.sel_compute_mode_segbtn.set("Monopolar")

        lbl_mode = ctk.CTkLabel(
            radius_mode_frame,
            text="Computation Mode:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        lbl_mode.pack(side="right", padx=(0,10))


        # Run SEEG ROI Mask Generation button
        run_seeg_roi_mask_tool_btn = ctk.CTkButton(
            SEEG_ROI_Mask_tool_frame,
            text="GENERATE SEEG ROI MASKS",
            height=45,
            fg_color="#6A5ACD",
            font=ctk.CTkFont(family="Proxima Nova", size=15, weight="bold"),
            command=lambda: self.start_seeg_roi_mask_thread()
        )
        run_seeg_roi_mask_tool_btn.grid(row=5, column=0, columnspan=3, pady=(20,30), padx=20, sticky="ew")
        

    def setup_settings_page(self):
        """Setup the settings page"""
        self.clear_main_pannel()
        self._save_current_page("settings")
        
        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")
        
        # Setup new page
        self.settings_page = ctk.CTkScrollableFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.settings_page.pack(fill="both", expand=True)
        self.settings_page.grid_columnconfigure(0, weight=1)
        
        # Page title
        title_label = ctk.CTkLabel(
            self.settings_page,
            text="Settings",
            font=ctk.CTkFont(family="Proxima Nova", size=24, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # External Dependencies Section
        deps_frame = ctk.CTkFrame(
            self.settings_page,
            fg_color=("white", "#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        deps_frame.grid(row=1, column=0, pady=20, padx=20, sticky="ew")
        deps_frame.columnconfigure(1, weight=1)
        
        deps_label = ctk.CTkLabel(
            deps_frame,
            text="External Dependencies (Auto-checked)",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        deps_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="w")
        
        # Check dependency status
        dep_status = self.settings_manager.get_dependency_status()
        
        row_idx = 1
        for dep_name, dep_info in dep_status.items():
            # Dependency name
            name_label = ctk.CTkLabel(
                deps_frame,
                text=f"{dep_name}:",
                font=ctk.CTkFont(family="Proxima Nova", size=14, weight="bold"),
                text_color=("gray30", "gray80")
            )
            name_label.grid(row=row_idx, column=0, padx=(20, 10), pady=10, sticky="w")
            
            # Status indicator
            if dep_info["available"]:
                status_text = "✓ Available"
                status_color = "green"
            else:
                status_text = "✗ Not Found"
                status_color = "red"
            
            status_label = ctk.CTkLabel(
                deps_frame,
                text=status_text,
                font=ctk.CTkFont(family="Proxima Nova", size=14),
                text_color=status_color
            )
            status_label.grid(row=row_idx, column=1, padx=10, pady=10, sticky="w")
            
            # Commands list
            row_idx += 1
            commands_text = "Commands: " + ", ".join(dep_info["commands"])
            commands_label = ctk.CTkLabel(
                deps_frame,
                text=commands_text,
                font=ctk.CTkFont(family="Proxima Nova", size=12),
                text_color=("gray40", "gray70")
            )
            commands_label.grid(row=row_idx, column=0, columnspan=3, padx=(40, 20), pady=(0, 10), sticky="w")
            
            row_idx += 1
        
        # Add timestamp of check
        check_time_label = ctk.CTkLabel(
            deps_frame,
            text=f"Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            font=ctk.CTkFont(family="Proxima Nova", size=11, slant="italic"),
            text_color=("gray50", "gray60")
        )
        check_time_label.grid(row=row_idx, column=0, columnspan=3, padx=20, pady=(5, 5), sticky="w")
        row_idx += 1
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            deps_frame,
            text="Refresh Status",
            height=35,
            fg_color="#0078D7",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            command=self.setup_settings_page
        )
        refresh_btn.grid(row=row_idx, column=0, columnspan=3, pady=(10, 20), padx=20, sticky="ew")
        
        # Appearance Settings Section
        appearance_frame = ctk.CTkFrame(
            self.settings_page,
            fg_color=("white", "#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        appearance_frame.grid(row=2, column=0, pady=20, padx=20, sticky="ew")
        appearance_frame.columnconfigure(1, weight=1)
        
        appearance_label = ctk.CTkLabel(
            appearance_frame,
            text="Appearance",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        appearance_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        # Appearance mode selector
        mode_label = ctk.CTkLabel(
            appearance_frame,
            text="Appearance Mode:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        mode_label.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="w")
        
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            appearance_frame,
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode
        )
        current_mode = self.settings_manager.get("appearance_mode", "System")
        self.appearance_mode_menu.set(current_mode)
        self.appearance_mode_menu.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="w")


    def setup_history_page(self):
        """Setup the task history page"""
        self.clear_main_pannel()
        self._save_current_page("history")
        
        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_1.configure(text="Tools ▼", fg_color="#0078D7")
        
        # Setup new page
        self.history_page = ctk.CTkFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.history_page.pack(fill="both", expand=True, padx=20, pady=20)
        self.history_page.grid_columnconfigure(0, weight=1)
        self.history_page.grid_rowconfigure(1, weight=1)
        
        # Page title and controls
        header_frame = ctk.CTkFrame(self.history_page, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Task History",
            font=ctk.CTkFont(family="Proxima Nova", size=24, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, padx=0, pady=0, sticky="w")
        
        clear_btn = ctk.CTkButton(
            header_frame,
            text="Clear History",
            height=35,
            fg_color="#DC3545",
            hover_color="#C82333",
            font=ctk.CTkFont(family="Proxima Nova", size=13),
            command=self.clear_task_history
        )
        clear_btn.grid(row=0, column=1, padx=10, pady=0, sticky="e")
        
        # Task history list
        history_list_frame = ctk.CTkScrollableFrame(
            self.history_page,
            fg_color=("white", "#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        history_list_frame.grid(row=1, column=0, sticky="nsew")
        history_list_frame.grid_columnconfigure(0, weight=1)
        
        # Get task history
        tasks = self.task_logger.get_recent_tasks(100)
        
        if not tasks:
            no_tasks_label = ctk.CTkLabel(
                history_list_frame,
                text="No task history yet",
                font=ctk.CTkFont(family="Proxima Nova", size=14),
                text_color=("gray40", "gray70")
            )
            no_tasks_label.grid(row=0, column=0, padx=20, pady=20)
        else:
            for idx, task in enumerate(tasks):
                self._create_task_entry(history_list_frame, idx, task)
    
    def _create_task_entry(self, parent, idx, task):
        """Create a single task entry in the history list"""
        task_frame = ctk.CTkFrame(
            parent,
            fg_color=("gray95", "#1E1E1E"),
            corner_radius=5,
            border_width=1,
            border_color=("#D0D0D0", "#404040")
        )
        task_frame.grid(row=idx, column=0, padx=10, pady=5, sticky="ew")
        task_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        status_colors = {
            "completed": "green",
            "running": "orange",
            "failed": "red",
            "interrupted": "orange"
        }
        status_color = status_colors.get(task["status"], "gray")
        
        status_label = ctk.CTkLabel(
            task_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color=status_color,
            width=30
        )
        status_label.grid(row=0, column=0, rowspan=4, padx=(10, 5), pady=10)
        
        # Task name and type
        name_label = ctk.CTkLabel(
            task_frame,
            text=f"{task['name']} ({task['type']})",
            font=ctk.CTkFont(family="Proxima Nova", size=14, weight="bold"),
            text_color=("gray10", "gray90"),
            anchor="w"
        )
        name_label.grid(row=0, column=1, padx=10, pady=(10, 2), sticky="w")
        
        # Time info
        try:
            start_time = datetime.fromisoformat(task["start_time"])
            time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            
            if task["end_time"]:
                end_time = datetime.fromisoformat(task["end_time"])
                duration = (end_time - start_time).total_seconds()
                time_str += f" | Duration: {duration:.1f}s"
        except:
            time_str = "Unknown time"
        
        time_label = ctk.CTkLabel(
            task_frame,
            text=time_str,
            font=ctk.CTkFont(family="Proxima Nova", size=11),
            text_color=("gray40", "gray70"),
            anchor="w"
        )
        time_label.grid(row=1, column=1, padx=10, pady=(2, 2), sticky="w")
        
        # Input files (if any)
        if task.get("input_files") and len(task["input_files"]) > 0:
            input_count = len(task["input_files"])
            if input_count <= 2:
                input_text = "Input: " + ", ".join([Path(f).name for f in task["input_files"]])
            else:
                first_file = Path(task["input_files"][0]).name
                input_text = f"Input: {first_file} and {input_count - 1} more file(s)"
            
            input_label = ctk.CTkLabel(
                task_frame,
                text=input_text,
                font=ctk.CTkFont(family="Proxima Nova", size=10),
                text_color=("gray50", "gray60"),
                anchor="w"
            )
            input_label.grid(row=2, column=1, padx=10, pady=(2, 2), sticky="w")
        
        # Output location (if any)
        if task.get("output_location"):
            output_text = f"Output: {task['output_location']}"
            output_label = ctk.CTkLabel(
                task_frame,
                text=output_text,
                font=ctk.CTkFont(family="Proxima Nova", size=10),
                text_color=("gray50", "gray60"),
                anchor="w"
            )
            output_label.grid(row=3, column=1, padx=10, pady=(2, 10), sticky="w")
        else:
            # Adjust padding if no output location
            time_label.grid(pady=(2, 10))
        
        # Status text
        status_text = task["status"].capitalize()
        if task.get("error_message"):
            status_text += f" - {task['error_message']}"
        
        status_text_label = ctk.CTkLabel(
            task_frame,
            text=status_text,
            font=ctk.CTkFont(family="Proxima Nova", size=12),
            text_color=("gray30", "gray80"),
            anchor="e"
        )
        status_text_label.grid(row=0, column=2, rowspan=4, padx=10, pady=10, sticky="e")
    
    def change_appearance_mode(self, new_mode):
        """Change application appearance mode"""
        ctk.set_appearance_mode(new_mode)
        self.settings_manager.set("appearance_mode", new_mode)
    
    def clear_task_history(self):
        """Clear all task history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all task history?"):
            self.task_logger.clear_history()
            self.setup_history_page()  # Refresh the page


### HELPER FUNCTIONS ###

# UI design functions

    def createrow(self, parent, row_idx, label_text, start_col=0, entry_span=1, use_textbox=False):
        lbl = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(family="Proxima Nova", size=14),
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
        
        # Log task start
        self.current_task_id = self.task_logger.start_task(
            "New Registration",
            "Registration",
            f"{len(moving_list)} image(s)",
            input_files=[fixed] + moving_list,
            output_location=out
        )
        
        self._show_task_status("New Registration")
        self.cancel_task_flag = False
        
        task = threading.Thread(target=XC_XFM_TOOLBOX.new_xfm, args=(out, fixed, moving_list, self.on_registration_complete), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_registration_complete(self):
        # Log task completion
        if self.current_task_id is not None:
            self.task_logger.complete_task(self.current_task_id, "completed")
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
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
            
            # Log task start
            self.current_task_id = self.task_logger.start_task(
                "Apply Transform",
                "Registration",
                f"{len(moving_list)} image(s)",
                input_files=moving_list + transform_list + [reference],
                output_location=out_dir
            )
            
            self._show_task_status("Apply Transform")
            self.cancel_task_flag = False

            task = threading.Thread(target=XC_XFM_TOOLBOX.apply_existing_xfm, args=(out_dir, transform_list, moving_list, reference, self.on_apply_transform_complete), daemon=True)
            self.current_task_thread = task
            task.start()

    def on_apply_transform_complete(self):
        # Log task completion
        if self.current_task_id is not None:
            self.task_logger.complete_task(self.current_task_id, "completed")
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        self.after(0,self.show_apply_transform_complete_message)
        
    def show_apply_transform_complete_message(self):
        messagebox.showinfo("Success", "Transform Application Complete")

## Connectome threading ##

# Generate connectome thread starter

    def start_connectome_thread(self):
        mask_image = self.entry_mask_img_cntcm.get().strip()

        raw_tracks = self.entry_tracks_cnctm.get("0.0", "end")
        tracks_list = [line.strip() for line in raw_tracks.split("\n") if line.strip()]

        raw_weights = self.entry_tracks_cnctm_weights.get("0.0", "end")
        tracks_weights_list = [line.strip() for line in raw_weights.split("\n") if line.strip()]

        output_dir = self.entry_output_cnctm.get().strip()

        if not mask_image or not tracks_list:
            messagebox.showerror("Input Error", "Please provide Mask Image, at least one Track file and an output directory.")
            return
        
        # Log task start
        self.current_task_id = self.task_logger.start_task(
            "Generate Connectomes",
            "Connectome",
            f"{len(tracks_list)} track(s)",
            input_files=[mask_image] + tracks_list + tracks_weights_list,
            output_location=output_dir
        )
        
        self._show_task_status("Generate Connectomes")
        self.cancel_task_flag = False

        task = threading.Thread(target=XC_CONNECTOME_TOOLBOX.gen_connectome, args=(mask_image, tracks_list, output_dir, tracks_weights_list, self.on_connectome_complete), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_connectome_complete(self):
        # Log task completion
        if self.current_task_id is not None:
            self.task_logger.complete_task(self.current_task_id, "completed")
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
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
        
        # Log task start
        self.current_task_id = self.task_logger.start_task(
            "Z-Score Connectome",
            "Connectome",
            f"{len(ref_connectomes_list)} reference(s)",
            input_files=[subject_connectome] + ref_connectomes_list,
            output_location=output_dir
        )
        
        self._show_task_status("Z-Score Connectome")
        self.cancel_task_flag = False

        task = threading.Thread(target=XC_CONNECTOME_TOOLBOX.z_scored_connectome, args=(subject_connectome, ref_connectomes_list, output_dir, self.on_z_score_complete), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_z_score_complete(self):
        # Log task completion
        if self.current_task_id is not None:
            self.task_logger.complete_task(self.current_task_id, "completed")
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
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
        
        # Log task start
        self.current_task_id = self.task_logger.start_task(
            "Display Connectomes",
            "Connectome",
            f"{len(cnctms_list)} connectome(s)",
            input_files=cnctms_list + luts_list,
            output_location="Display only"
        )
        
        self._show_task_status("Display Connectomes")
        self.cancel_task_flag = False
        
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

        task = threading.Thread(target=XC_CONNECTOME_TOOLBOX.display_connectome, args=(paired_data, self.on_display_complete), daemon=True)
        self.current_task_thread = task
        task.start()
    
    def on_display_complete(self):
        # Log task completion
        if self.current_task_id is not None:
            self.task_logger.complete_task(self.current_task_id, "completed")
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
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
        
        # Log task start
        self.current_task_id = self.task_logger.start_task(
            "Generate SEEG ROI Masks",
            "ROI Toolbox",
            f"Mode: {raw_mode}, Radius: {sel_rad}mm",
            input_files=[ref_mask_img, seeg_coords_file],
            output_location=output_dir
        )
        
        self._show_task_status("Generate SEEG ROI Masks")
        self.cancel_task_flag = False

        task = threading.Thread(target=XC_ROI_TOOLBOX.generate_seeg_roi_masks, args=(ref_mask_img, seeg_coords_file, output_dir, sel_rad, is_bipolar_mode, self.on_seeg_roi_mask_complete), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_seeg_roi_mask_complete(self):
        # Log task completion
        if self.current_task_id is not None:
            self.task_logger.complete_task(self.current_task_id, "completed")
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        self.after(0,self.show_seeg_roi_mask_complete_message)

    def show_seeg_roi_mask_complete_message(self):
        messagebox.showinfo("Success", "SEEG ROI Mask Generation Complete")

# MAIN LOOP #        
if __name__ == "__main__":
    app = CLAP()
    app.mainloop()