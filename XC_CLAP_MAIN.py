import customtkinter as ctk
import sys
import os
from pathlib import Path
import threading
import subprocess
import platform
import shlex
from tkinter import filedialog, messagebox
from PIL import Image
from datetime import datetime
import XC_XFM_TOOLBOX
import XC_CONNECTOME_TOOLBOX
import XC_ROI_TOOLBOX
import XC_SEGMENTATION_TOOLBOX
import pygame
from clap_settings import SettingsManager
from clap_task_logger import TaskLogger
from script_registry import ScriptRegistry

class CLAP(ctk.CTk):
    # Tag colors for UI display (light mode, dark mode)
    TAG_COLORS = {
        'analysis': ("#D4EDDA", "#155724"),   # Green
        'statistics': ("#CCE5FF", "#004085"), # Blue
        'setup': ("#F8D7DA", "#721C24"),      # Red
        'other': ("#E2D9F3", "#3D1A5F")       # Purple
    }
    
    def __init__(self):
        super().__init__()

        pygame.mixer.init()
        
        # Initialize settings and task logger
        self.settings_manager = SettingsManager()
        self.task_logger = TaskLogger()
        self.script_registry = ScriptRegistry()
        self.current_task_thread = None
        self.current_task_id = None
        self.cancel_task_flag = False
        
        # Store form field values to preserve across page changes
        self.form_values = {}

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

        logo_label = ctk.CTkLabel(sidebar_title_card, text="C.L.A.P.", font=ctk.CTkFont(size=20, weight="bold"),corner_radius=0)
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
        sidebar_button_card.grid_rowconfigure(1, weight=1)  # Spacer row

        # Home button at the top
        self.sidebar_btn_home = ctk.CTkButton(sidebar_button_card, text="Home", fg_color="#0078D7", command=self.setup_home_page)
        self.sidebar_btn_home.grid(row=0, column=0, padx=5, pady=10)
        
        # Tools drawer (will appear above bottom buttons when opened)
        self.tools_drawer = ctk.CTkFrame(sidebar_button_card, fg_color="transparent")

        self.tools_btn_registration = ctk.CTkButton(self.tools_drawer, text="Registration tools", command=self.setup_registration_tools_page)
        self.tools_btn_registration.pack(fill="x", padx=10, pady=5)

        self.tools_btn_connectome = ctk.CTkButton(self.tools_drawer, text="Connectome Toolbox", command=self.setup_connectome_toolbox_page)
        self.tools_btn_connectome.pack(fill="x", padx=10, pady=5)

        self.tools_btn_roi = ctk.CTkButton(self.tools_drawer, text="ROI Parcelation Toolbox", command=self.setup_ROI_toolbox_page)
        self.tools_btn_roi.pack(fill="x", padx=10, pady=5)

        self.tools_btn_segmentation = ctk.CTkButton(self.tools_drawer, text="Segmentation Toolbox", command=self.setup_segmentation_toolbox_page)
        self.tools_btn_segmentation.pack(fill="x", padx=10, pady=5)
        
        self.tools_btn_script_repo = ctk.CTkButton(self.tools_drawer, text="Script Repository", command=self.setup_script_repository_page)
        self.tools_btn_script_repo.pack(fill="x", padx=10, pady=5)
        
        # Bottom buttons (Tools, Settings, History)
        self.sidebar_btn_tools = ctk.CTkButton(sidebar_button_card, text="Tools", fg_color="#0078D7", command=self.toggle_tools_menu)
        self.sidebar_btn_tools.grid(row=2, column=0, padx=5, pady=10)
        
        self.sidebar_btn_settings = ctk.CTkButton(sidebar_button_card, text="Settings", fg_color="#0078D7", command=self.setup_settings_page)
        self.sidebar_btn_settings.grid(row=3, column=0, padx=5, pady=10)
        
        self.sidebar_btn_history = ctk.CTkButton(sidebar_button_card, text="History", fg_color="#0078D7", command=self.setup_history_page)
        self.sidebar_btn_history.grid(row=4, column=0, padx=5, pady=10)
        
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
            self.sidebar_btn_tools.configure(text="Tools", fg_color="#0078D7")
            self.settings_manager.set("tools_menu_expanded", False)
        else:
            self.tools_drawer.grid(row=1, column=0, sticky="sew", pady=(0, 10))
            self.sidebar_btn_tools.configure(text="Tools", fg_color="#004E81")
            self.settings_manager.set("tools_menu_expanded", True)
    
    def _restore_ui_state(self):
        """Restore UI state from settings"""
        # Restore menu expansion state
        if self.settings_manager.get("tools_menu_expanded", False):
            self.tools_drawer.grid(row=1, column=0, sticky="sew", pady=(0, 10))
            self.sidebar_btn_tools.configure(text="Tools", fg_color="#004E81")
        
        # Restore last page
        last_page = self.settings_manager.get("last_page", "home")
        page_methods = {
            "home": self.setup_home_page,
            "registration": self.setup_registration_tools_page,
            "connectome": self.setup_connectome_toolbox_page,
            "roi": self.setup_ROI_toolbox_page,
            "segmentation": self.setup_segmentation_toolbox_page,
            "script_repository": self.setup_script_repository_page,
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
        
        This marks the task as cancelled and signals the background thread to terminate
        any running subprocess. The cancellation is checked periodically in the task
        execution functions.
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
    
    def _save_form_value(self, field_name, widget):
        """Save the value of a form field"""
        if widget is None:
            return
        
        try:
            # Handle different widget types
            if hasattr(widget, 'get'):
                value = widget.get()
                # For textboxes, get() method is called directly with arguments
                if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                    # Check if it's a textbox by trying to get with textbox arguments
                    try:
                        value = widget.get("0.0", "end").strip()
                    except:
                        # It's an Entry widget, value is already retrieved
                        pass
                self.form_values[field_name] = value
        except Exception:
            pass
    
    def _restore_form_value(self, field_name, widget):
        """Restore the value of a form field"""
        if field_name not in self.form_values or widget is None:
            return
        
        try:
            value = self.form_values[field_name]
            if not value:
                return
            
            # Handle different widget types
            if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                # For Entry widgets
                if hasattr(widget, 'get') and not callable(widget.get()):
                    widget.delete(0, "end")
                    widget.insert(0, value)
                # For Textbox widgets
                else:
                    widget.delete("0.0", "end")
                    widget.insert("0.0", value)
        except Exception:
            pass
    
    def _save_page_form_values(self, page_name):
        """Save all form values for a specific page before destroying it"""
        # Define field mappings for each page
        page_field_mappings = {
            "registration": {
                "prefix": "reg_",
                "fields": [
                    ('reg_destination_space', 'entry_destination_space'),
                    ('reg_moving', 'entry_moving'),
                    ('reg_output', 'entry_output_reg'),
                    ('reg_moving_apply', 'entry_moving_apply'),
                    ('reg_transform_file', 'entry_transform_file'),
                    ('reg_reference_apply', 'entry_reference_apply'),
                    ('reg_output_apply', 'entry_output_apply'),
                ]
            },
            "connectome": {
                "prefix": "con_",
                "fields": [
                    ('con_mask_img', 'entry_mask_img_cntcm'),
                    ('con_tracks', 'entry_tracks_cnctm'),
                    ('con_tracks_weights', 'entry_tracks_cnctm_weights'),
                    ('con_output', 'entry_output_cnctm'),
                    ('con_sub_connectome', 'entry_sub_connectome'),
                    ('con_ref_connectomes', 'entry_ref_connectomes'),
                    ('con_output_zscore', 'entry_output_zscore_cnctm'),
                    ('con_disp_cnctm', 'entry_disp_cnctm'),
                    ('con_disp_lut', 'entry_disp_lut'),
                ]
            },
            "roi": {
                "prefix": "roi_",
                "fields": [
                    ('roi_ref_mask_img', 'entry_ref_mask_img'),
                    ('roi_seeg_coords', 'entry_seeg_coords'),
                    ('roi_output_dir', 'entry_output_roi_mask_dir'),
                    ('roi_radius', 'sel_compute_radius'),
                ]
            },
            "segmentation": {
                "prefix": "seg_",
                "fields": [
                    ('seg_freeview_images', 'entry_freeview_images'),
                    ('seg_recon_input', 'entry_recon_input'),
                    ('seg_recon_subject_id', 'entry_recon_subject_id'),
                    ('seg_recon_output', 'entry_recon_output'),
                    ('seg_fastsurfer_input', 'entry_fastsurfer_input'),
                    ('seg_fastsurfer_subject_id', 'entry_fastsurfer_subject_id'),
                    ('seg_fastsurfer_output', 'entry_fastsurfer_output'),
                ]
            }
        }
        
        if page_name not in page_field_mappings:
            return
        
        mapping = page_field_mappings[page_name]
        
        # Clear previous values for this page
        self.form_values = {k: v for k, v in self.form_values.items() if not k.startswith(mapping["prefix"])}
        
        # Save field values
        for field_key, widget_attr in mapping["fields"]:
            if hasattr(self, widget_attr):
                self._save_form_value(field_key, getattr(self, widget_attr))
        
        # Special handling for ROI mode (SegmentedButton)
        if page_name == "roi" and hasattr(self, 'sel_compute_mode_segbtn'):
            try:
                self.form_values['roi_mode'] = self.sel_compute_mode_segbtn.get()
            except Exception:
                pass
        
        # Special handling for FastSurfer GPU toggle (CheckBox)
        if page_name == "segmentation" and hasattr(self, 'fastsurfer_gpu_toggle'):
            try:
                self.form_values['seg_fastsurfer_gpu'] = self.fastsurfer_gpu_toggle.get()
            except Exception:
                pass


#### Page Setups ####

    def setup_home_page(self):
        # Save current page values before clearing
        last_page = self.settings_manager.get("last_page", "home")
        if last_page in ["registration", "connectome", "roi", "segmentation"]:
            self._save_page_form_values(last_page)
        
        self.clear_main_pannel()
        self._save_current_page("home")

        self.home_page = ctk.CTkFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.home_page.pack(fill="both", expand=True)

        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_tools.configure(text="Tools", fg_color="#0078D7")

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
        # Save current page values before clearing
        last_page = self.settings_manager.get("last_page", "home")
        if last_page in ["registration", "connectome", "roi", "segmentation"]:
            self._save_page_form_values(last_page)

        # Remove previous page
        self.clear_main_pannel()
        self._save_current_page("registration")

        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_tools.configure(text="Tools", fg_color="#0078D7")

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

        # Restore saved form values
        self._restore_form_value('reg_destination_space', self.entry_destination_space)
        self._restore_form_value('reg_moving', self.entry_moving)
        self._restore_form_value('reg_output', self.entry_output_reg)
        self._restore_form_value('reg_moving_apply', self.entry_moving_apply)
        self._restore_form_value('reg_transform_file', self.entry_transform_file)
        self._restore_form_value('reg_reference_apply', self.entry_reference_apply)
        self._restore_form_value('reg_output_apply', self.entry_output_apply)


    def setup_connectome_toolbox_page(self):
        # Save current page values before clearing
        last_page = self.settings_manager.get("last_page", "home")
        if last_page in ["registration", "connectome", "roi", "segmentation"]:
            self._save_page_form_values(last_page)

        # Remove previous page
        self.clear_main_pannel()
        self._save_current_page("connectome")

        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_tools.configure(text="Tools", fg_color="#0078D7")

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

        # Restore saved form values
        self._restore_form_value('con_mask_img', self.entry_mask_img_cntcm)
        self._restore_form_value('con_tracks', self.entry_tracks_cnctm)
        self._restore_form_value('con_tracks_weights', self.entry_tracks_cnctm_weights)
        self._restore_form_value('con_output', self.entry_output_cnctm)
        self._restore_form_value('con_sub_connectome', self.entry_sub_connectome)
        self._restore_form_value('con_ref_connectomes', self.entry_ref_connectomes)
        self._restore_form_value('con_output_zscore', self.entry_output_zscore_cnctm)
        self._restore_form_value('con_disp_cnctm', self.entry_disp_cnctm)
        self._restore_form_value('con_disp_lut', self.entry_disp_lut)


    def setup_ROI_toolbox_page(self):
        # Save current page values before clearing
        last_page = self.settings_manager.get("last_page", "home")
        if last_page in ["registration", "connectome", "roi", "segmentation"]:
            self._save_page_form_values(last_page)

        # Remove previous page
        self.clear_main_pannel()
        self._save_current_page("roi")

        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_tools.configure(text="Tools", fg_color="#0078D7")

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

        lbl_mode = ctk.CTkLabel(
            radius_mode_frame,
            text="Computation Mode:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        lbl_mode.pack(side="left", padx=(20,0))

        self.sel_compute_mode_segbtn = ctk.CTkSegmentedButton(
            radius_mode_frame,
            values=["Monopolar", "Bipolar"],
            fg_color=("gray85", "gray15"),
            unselected_color=("gray85", "gray15"),
            selected_color="#0078D7",
            font=ctk.CTkFont(family="Proxima Nova", size=13),
            corner_radius=8,
        )
        self.sel_compute_mode_segbtn.pack(side="left", padx=(10,0))
        self.sel_compute_mode_segbtn.set("Monopolar")

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
        
        # Restore saved form values
        self._restore_form_value('roi_ref_mask_img', self.entry_ref_mask_img)
        self._restore_form_value('roi_seeg_coords', self.entry_seeg_coords)
        self._restore_form_value('roi_output_dir', self.entry_output_roi_mask_dir)
        self._restore_form_value('roi_radius', self.sel_compute_radius)
        if 'roi_mode' in self.form_values:
            try:
                self.sel_compute_mode_segbtn.set(self.form_values['roi_mode'])
            except Exception:
                pass


    def setup_segmentation_toolbox_page(self):
        """Setup the segmentation toolbox page for FreeSurfer/FastSurfer"""
        # Save current page values before clearing
        last_page = self.settings_manager.get("last_page", "home")
        if last_page in ["registration", "connectome", "roi", "segmentation"]:
            self._save_page_form_values(last_page)

        # Remove previous page
        self.clear_main_pannel()
        self._save_current_page("segmentation")

        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_tools.configure(text="Tools", fg_color="#0078D7")

        # Setup new page
        self.segmentation_toolbox_page = ctk.CTkScrollableFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.segmentation_toolbox_page.pack(fill="both", expand=True)

        self.segmentation_toolbox_page.columnconfigure(0, weight=1)

        # Launch Freeview Tool #

        # Frame for tool
        freeview_frame = ctk.CTkFrame(
            self.segmentation_toolbox_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        freeview_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        freeview_frame.columnconfigure(1, weight=1)

        # Label for tool
        freeview_label = ctk.CTkLabel(
            freeview_frame,
            text="Launch FreeSurfer Freeview",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        freeview_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,10), sticky="w")

        # Select images to view
        self.entry_freeview_images, freeview_images_btn = self.createrow(freeview_frame, 1, "Image(s) to view:", use_textbox=True)
        freeview_images_btn.configure(command=lambda: self.browse_files(self.entry_freeview_images))

        # Launch freeview button
        launch_freeview_btn = ctk.CTkButton(
            freeview_frame,
            text="LAUNCH FREEVIEW",
            height=45,
            fg_color="#6A5ACD",
            font=ctk.CTkFont(family="Proxima Nova", size=15, weight="bold"),
            command=lambda: self.start_freeview_thread()
        )
        launch_freeview_btn.grid(row=2, column=0, columnspan=3, pady=(20,30), padx=20, sticky="ew")


        # Run FreeSurfer recon-all Tool #

        # Frame for tool
        recon_all_frame = ctk.CTkFrame(
            self.segmentation_toolbox_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        recon_all_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        recon_all_frame.columnconfigure(1, weight=1)

        # Label for tool
        recon_all_label = ctk.CTkLabel(
            recon_all_frame,
            text="Run FreeSurfer recon-all",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        recon_all_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,10), sticky="w")

        # Select input T1 image
        self.entry_recon_input, recon_input_btn = self.createrow(recon_all_frame, 1, "Input T1 Image:")
        recon_input_btn.configure(command=lambda: self.browse_file_and_update_subject_id(self.entry_recon_input, self.entry_recon_subject_id))

        # Subject ID with auto-fill button
        lbl_recon_subj = ctk.CTkLabel(
            recon_all_frame,
            text="Subject ID:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        lbl_recon_subj.grid(row=2, column=0, padx=(20,10), pady=10, sticky="w")

        self.entry_recon_subject_id = ctk.CTkEntry(
            recon_all_frame,
            height=35,
            border_color=("#D0D0D0", "#505050"), 
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        self.entry_recon_subject_id.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        auto_fill_recon_btn = ctk.CTkButton(
            recon_all_frame,
            text="Auto-fill",
            width=80,
            height=35,
            fg_color=("#F0F0F0", "#3A3A3A"),
            text_color=("black", "white"),
            hover_color=("#D9D9D9", "#505050"),
            command=lambda: self.auto_fill_subject_id(self.entry_recon_input, self.entry_recon_subject_id)
        )
        auto_fill_recon_btn.grid(row=2, column=2, padx=(0,20), pady=10)

        # Select output directory (SUBJECTS_DIR)
        self.entry_recon_output, recon_output_btn = self.createrow(recon_all_frame, 3, "Output Directory (SUBJECTS_DIR):")
        recon_output_btn.configure(command=lambda: self.browse_folder(self.entry_recon_output))

        # Run recon-all button
        run_recon_all_btn = ctk.CTkButton(
            recon_all_frame,
            text="RUN RECON-ALL",
            height=45,
            fg_color="#6A5ACD",
            font=ctk.CTkFont(family="Proxima Nova", size=15, weight="bold"),
            command=lambda: self.start_recon_all_thread()
        )
        run_recon_all_btn.grid(row=4, column=0, columnspan=3, pady=(20,30), padx=20, sticky="ew")


        # Run FastSurfer Tool #

        # Frame for tool
        fastsurfer_frame = ctk.CTkFrame(
            self.segmentation_toolbox_page,
            fg_color=("white","#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        fastsurfer_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        fastsurfer_frame.columnconfigure(1, weight=1)

        # Label for tool
        fastsurfer_label = ctk.CTkLabel(
            fastsurfer_frame,
            text="Run FastSurfer",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        fastsurfer_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,10), sticky="w")

        # Select input T1 image
        self.entry_fastsurfer_input, fastsurfer_input_btn = self.createrow(fastsurfer_frame, 1, "Input T1 Image:")
        fastsurfer_input_btn.configure(command=lambda: self.browse_file_and_update_subject_id(self.entry_fastsurfer_input, self.entry_fastsurfer_subject_id))

        # Subject ID with auto-fill button
        lbl_fastsurfer_subj = ctk.CTkLabel(
            fastsurfer_frame,
            text="Subject ID:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        lbl_fastsurfer_subj.grid(row=2, column=0, padx=(20,10), pady=10, sticky="w")

        self.entry_fastsurfer_subject_id = ctk.CTkEntry(
            fastsurfer_frame,
            height=35,
            border_color=("#D0D0D0", "#505050"), 
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        self.entry_fastsurfer_subject_id.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        auto_fill_fastsurfer_btn = ctk.CTkButton(
            fastsurfer_frame,
            text="Auto-fill",
            width=80,
            height=35,
            fg_color=("#F0F0F0", "#3A3A3A"),
            text_color=("black", "white"),
            hover_color=("#D9D9D9", "#505050"),
            command=lambda: self.auto_fill_subject_id(self.entry_fastsurfer_input, self.entry_fastsurfer_subject_id)
        )
        auto_fill_fastsurfer_btn.grid(row=2, column=2, padx=(0,20), pady=10)

        # Select output directory (SUBJECTS_DIR)
        self.entry_fastsurfer_output, fastsurfer_output_btn = self.createrow(fastsurfer_frame, 3, "Output Directory (SUBJECTS_DIR):")
        fastsurfer_output_btn.configure(command=lambda: self.browse_folder(self.entry_fastsurfer_output))

        # GPU toggle
        gpu_toggle_frame = ctk.CTkFrame(fastsurfer_frame, fg_color="transparent")
        gpu_toggle_frame.grid(row=4, column=0, columnspan=3, padx=20, pady=(10,0), sticky="w")
        
        self.fastsurfer_gpu_toggle = ctk.CTkCheckBox(
            gpu_toggle_frame,
            text="Use GPU acceleration",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        self.fastsurfer_gpu_toggle.select()  # Default to enabled
        self.fastsurfer_gpu_toggle.pack(side="left")

        # Run FastSurfer button
        run_fastsurfer_btn = ctk.CTkButton(
            fastsurfer_frame,
            text="RUN FASTSURFER",
            height=45,
            fg_color="#6A5ACD",
            font=ctk.CTkFont(family="Proxima Nova", size=15, weight="bold"),
            command=lambda: self.start_fastsurfer_thread()
        )
        run_fastsurfer_btn.grid(row=5, column=0, columnspan=3, pady=(20,30), padx=20, sticky="ew")

        # Restore saved form values
        self._restore_form_value('seg_freeview_images', self.entry_freeview_images)
        self._restore_form_value('seg_recon_input', self.entry_recon_input)
        self._restore_form_value('seg_recon_subject_id', self.entry_recon_subject_id)
        self._restore_form_value('seg_recon_output', self.entry_recon_output)
        self._restore_form_value('seg_fastsurfer_input', self.entry_fastsurfer_input)
        self._restore_form_value('seg_fastsurfer_subject_id', self.entry_fastsurfer_subject_id)
        self._restore_form_value('seg_fastsurfer_output', self.entry_fastsurfer_output)
        
        # Restore GPU toggle state
        if 'seg_fastsurfer_gpu' in self.form_values:
            try:
                if self.form_values['seg_fastsurfer_gpu'] == 1:
                    self.fastsurfer_gpu_toggle.select()
                else:
                    self.fastsurfer_gpu_toggle.deselect()
            except Exception:
                pass


    def setup_script_repository_page(self):
        """Setup the script repository page"""
        # Save current page values before clearing
        last_page = self.settings_manager.get("last_page", "home")
        if last_page in ["registration", "connectome", "roi", "segmentation"]:
            self._save_page_form_values(last_page)
        
        self.clear_main_pannel()
        self._save_current_page("script_repository")
        
        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_tools.configure(text="Tools", fg_color="#0078D7")
        
        # Setup new page
        self.script_repository_page = ctk.CTkFrame(self.main_pannel, corner_radius=0, fg_color="transparent")
        self.script_repository_page.pack(fill="both", expand=True, padx=20, pady=20)
        self.script_repository_page.grid_columnconfigure(0, weight=1)
        self.script_repository_page.grid_rowconfigure(1, weight=1)
        
        # Header with title and add button
        header_frame = ctk.CTkFrame(self.script_repository_page, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Script Repository",
            font=ctk.CTkFont(family="Proxima Nova", size=24, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, padx=0, pady=0, sticky="w")
        
        add_script_btn = ctk.CTkButton(
            header_frame,
            text="Add New Script",
            height=35,
            fg_color="#28A745",
            hover_color="#218838",
            font=ctk.CTkFont(family="Proxima Nova", size=13, weight="bold"),
            command=self.open_add_script_dialog
        )
        add_script_btn.grid(row=0, column=1, padx=10, pady=0, sticky="e")
        
        # Filter bar
        filter_frame = ctk.CTkFrame(
            self.script_repository_page,
            fg_color=("white", "#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(40, 10))
        filter_frame.grid_columnconfigure(4, weight=1)
        
        # Project filter
        ctk.CTkLabel(
            filter_frame,
            text="Project:",
            font=ctk.CTkFont(family="Proxima Nova", size=12),
            text_color=("gray30", "gray80")
        ).grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        
        projects = ["All"] + self.script_registry.get_unique_projects()
        self.project_filter = ctk.CTkOptionMenu(
            filter_frame,
            values=projects,
            width=120,
            command=lambda _: self.refresh_script_list()
        )
        self.project_filter.set("All")
        self.project_filter.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="w")
        
        # Language filter
        ctk.CTkLabel(
            filter_frame,
            text="Language:",
            font=ctk.CTkFont(family="Proxima Nova", size=12),
            text_color=("gray30", "gray80")
        ).grid(row=0, column=2, padx=(10, 5), pady=10, sticky="w")
        
        languages = ["All"] + self.script_registry.get_unique_languages()
        self.language_filter = ctk.CTkOptionMenu(
            filter_frame,
            values=languages,
            width=120,
            command=lambda _: self.refresh_script_list()
        )
        self.language_filter.set("All")
        self.language_filter.grid(row=0, column=3, padx=(0, 10), pady=10, sticky="w")
        
        # Search box
        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Search scripts...",
            height=30,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        self.search_entry.grid(row=0, column=4, padx=10, pady=10, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_script_list())
        
        # Scripts list container
        self.scripts_list_frame = ctk.CTkScrollableFrame(
            self.script_repository_page,
            fg_color=("white", "#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        self.scripts_list_frame.grid(row=1, column=0, sticky="nsew")
        self.scripts_list_frame.grid_columnconfigure(0, weight=1)
        
        # Load scripts
        self.refresh_script_list()
    
    def refresh_script_list(self):
        """Refresh the scripts list based on current filters"""
        # Clear current list
        for widget in self.scripts_list_frame.winfo_children():
            widget.destroy()
        
        # Get filter values
        project = self.project_filter.get() if self.project_filter.get() != "All" else None
        language = self.language_filter.get() if self.language_filter.get() != "All" else None
        search_term = self.search_entry.get().strip() if self.search_entry.get() else None
        
        # Get filtered scripts
        scripts = self.script_registry.filter_scripts(
            project=project,
            language=language,
            search_term=search_term
        )
        
        if not scripts:
            no_scripts_label = ctk.CTkLabel(
                self.scripts_list_frame,
                text="No scripts found" if (project or language or search_term) else "No scripts in repository. Click 'Add New Script' to get started.",
                font=ctk.CTkFont(family="Proxima Nova", size=14),
                text_color=("gray40", "gray70")
            )
            no_scripts_label.grid(row=0, column=0, padx=20, pady=20)
        else:
            for idx, script in enumerate(scripts):
                self._create_script_card(self.scripts_list_frame, idx, script)
    
    def _create_script_card(self, parent, idx, script):
        """Create a script card in the list"""
        card_frame = ctk.CTkFrame(
            parent,
            fg_color=("gray95", "#1E1E1E"),
            corner_radius=5,
            border_width=1,
            border_color=("#D0D0D0", "#404040")
        )
        card_frame.grid(row=idx, column=0, padx=10, pady=5, sticky="ew")
        card_frame.grid_columnconfigure(1, weight=1)
        
        # Make card clickable
        card_frame.bind("<Button-1>", lambda e: self.open_script_inspector(script))
        
        # Script name (header)
        name_label = ctk.CTkLabel(
            card_frame,
            text=script.get("name", "Unknown"),
            font=ctk.CTkFont(family="Proxima Nova", size=16, weight="bold"),
            text_color=("gray10", "gray90"),
            anchor="w"
        )
        name_label.grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 5), sticky="w")
        name_label.bind("<Button-1>", lambda e: self.open_script_inspector(script))
        
        # Description
        description = script.get("description", "No description")
        if len(description) > 100:
            description = description[:100] + "..."
        
        desc_label = ctk.CTkLabel(
            card_frame,
            text=description,
            font=ctk.CTkFont(family="Proxima Nova", size=12),
            text_color=("gray40", "gray70"),
            anchor="w",
            wraplength=600
        )
        desc_label.grid(row=1, column=0, columnspan=3, padx=15, pady=(0, 8), sticky="w")
        desc_label.bind("<Button-1>", lambda e: self.open_script_inspector(script))
        
        # Badges row
        badges_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        badges_frame.grid(row=2, column=0, padx=15, pady=(0, 12), sticky="w")
        
        # Project badge
        if script.get("project"):
            project_badge = ctk.CTkLabel(
                badges_frame,
                text=script['project'],
                font=ctk.CTkFont(family="Proxima Nova", size=10),
                text_color=("gray10", "gray90"),
                fg_color=("#E3F2FD", "#1E3A5F"),
                corner_radius=5,
                padx=8,
                pady=2
            )
            project_badge.pack(side="left", padx=(0, 5))
        
        # Language badge
        language = script.get("language", "Unknown")
        
        language_badge = ctk.CTkLabel(
            badges_frame,
            text=language,
            font=ctk.CTkFont(family="Proxima Nova", size=10),
            text_color=("gray10", "gray90"),
            fg_color=("#FFF9C4", "#4A4A1A"),
            corner_radius=5,
            padx=8,
            pady=2
        )
        language_badge.pack(side="left", padx=(0, 5))
        
        # Author badge
        if script.get("author"):
            author_badge = ctk.CTkLabel(
                badges_frame,
                text=script['author'],
                font=ctk.CTkFont(family="Proxima Nova", size=10),
                text_color=("gray10", "gray90"),
                fg_color=("#E8F5E9", "#1B3E1F"),
                corner_radius=5,
                padx=8,
                pady=2
            )
            author_badge.pack(side="left", padx=(0, 5))
        
        # Tag badges
        tags = script.get("tags", [])
        if tags:
            for tag in tags:
                colors = self.TAG_COLORS.get(tag, ("#E0E0E0", "#404040"))
                tag_badge = ctk.CTkLabel(
                    badges_frame,
                    text=tag.upper(),
                    font=ctk.CTkFont(family="Proxima Nova", size=9, weight="bold"),
                    text_color=("gray10", "gray90"),
                    fg_color=colors,
                    corner_radius=5,
                    padx=8,
                    pady=2
                )
                tag_badge.pack(side="left", padx=(0, 5))
    
    def open_add_script_dialog(self):
        """Open dialog to add a new script"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Script")
        dialog.geometry("600x650")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (650 // 2)
        dialog.geometry(f"600x650+{x}+{y}")
        
        # Main container
        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        container.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            container,
            text="Import Script to Repository",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")
        
        # File selection
        ctk.CTkLabel(
            container,
            text="Script File:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        ).grid(row=1, column=0, padx=(0, 10), pady=10, sticky="w")
        
        file_entry = ctk.CTkEntry(
            container,
            height=35,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        file_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        def browse_script_file():
            filetypes = [
                ("All Script Files", "*.py *.sh *.R *.r *.m *.js *.pl *.rb"),
                ("Python Files", "*.py"),
                ("Bash Scripts", "*.sh"),
                ("R Scripts", "*.R *.r"),
                ("Matlab Scripts", "*.m"),
                ("JavaScript Files", "*.js"),
                ("All Files", "*.*")
            ]
            path = filedialog.askopenfilename(title="Select Script File", filetypes=filetypes)
            if path:
                file_entry.delete(0, ctk.END)
                file_entry.insert(0, path)
                
                # Auto-detect language
                language = self.script_registry.detect_language(path)
                language_entry.delete(0, ctk.END)
                language_entry.insert(0, language)
                
                # Auto-extract description
                description = self.script_registry.extract_description_from_file(path)
                if description:
                    description_text.delete("0.0", "end")
                    description_text.insert("0.0", description)
                
                # Auto-fill author from git config or environment
                if not author_entry.get():
                    try:
                        result = subprocess.run(
                            ["git", "config", "user.name"],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        if result.returncode == 0:
                            git_user = result.stdout.strip()
                            if git_user:
                                author_entry.delete(0, ctk.END)
                                author_entry.insert(0, git_user)
                    except:
                        pass
        
        browse_btn = ctk.CTkButton(
            container,
            text="Browse...",
            width=100,
            height=35,
            fg_color=("#F0F0F0", "#3A3A3A"),
            text_color=("black", "white"),
            hover_color=("#D9D9D9", "#505050"),
            command=browse_script_file
        )
        browse_btn.grid(row=1, column=2, padx=(0, 0), pady=10)
        
        # Language
        ctk.CTkLabel(
            container,
            text="Language:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        ).grid(row=2, column=0, padx=(0, 10), pady=10, sticky="w")
        
        language_entry = ctk.CTkEntry(
            container,
            height=35,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        language_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Project
        ctk.CTkLabel(
            container,
            text="Project:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        ).grid(row=3, column=0, padx=(0, 10), pady=10, sticky="w")
        
        existing_projects = self.script_registry.get_unique_projects()
        project_values = ["<New Project>"] + existing_projects
        
        project_combobox = ctk.CTkComboBox(
            container,
            values=project_values,
            height=35,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        project_combobox.set("<New Project>")
        project_combobox.grid(row=3, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Description
        ctk.CTkLabel(
            container,
            text="Description:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        ).grid(row=4, column=0, padx=(0, 10), pady=10, sticky="nw")
        
        description_text = ctk.CTkTextbox(
            container,
            height=100,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        description_text.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Dependencies
        ctk.CTkLabel(
            container,
            text="Dependencies:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        ).grid(row=5, column=0, padx=(0, 10), pady=10, sticky="w")
        
        dependencies_entry = ctk.CTkEntry(
            container,
            height=35,
            placeholder_text="e.g., numpy, pandas, scipy",
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        dependencies_entry.grid(row=5, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Author
        ctk.CTkLabel(
            container,
            text="Author:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        ).grid(row=6, column=0, padx=(0, 10), pady=10, sticky="w")
        
        author_entry = ctk.CTkEntry(
            container,
            height=35,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        author_entry.grid(row=6, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # Tags
        ctk.CTkLabel(
            container,
            text="Tags:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        ).grid(row=7, column=0, padx=(0, 10), pady=10, sticky="nw")
        
        # Tags frame with checkboxes
        tags_frame = ctk.CTkFrame(container, fg_color="transparent")
        tags_frame.grid(row=7, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        tag_checkboxes = {}
        tag_options = [
            ("analysis", "Analysis"),
            ("statistics", "Statistics"),
            ("setup", "Setup"),
            ("other", "Other")
        ]
        
        for i, (tag_value, tag_label) in enumerate(tag_options):
            cb = ctk.CTkCheckBox(
                tags_frame,
                text=tag_label,
                font=ctk.CTkFont(family="Proxima Nova", size=13),
                text_color=("gray30", "gray80")
            )
            cb.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="w")
            tag_checkboxes[tag_value] = cb
        
        # Buttons
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.grid(row=8, column=0, columnspan=3, pady=(20, 0), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        def save_script():
            # Validate inputs
            file_path = file_entry.get().strip()
            if not file_path:
                messagebox.showerror("Error", "Please select a script file.")
                return
            
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "Selected file does not exist.")
                return
            
            language = language_entry.get().strip()
            project = project_combobox.get().strip()
            description = description_text.get("0.0", "end").strip()
            dependencies = dependencies_entry.get().strip()
            author = author_entry.get().strip()
            
            # Collect selected tags
            selected_tags = [tag for tag, cb in tag_checkboxes.items() if cb.get() == 1]
            
            if not language:
                messagebox.showerror("Error", "Please specify the language.")
                return
            
            if not project or project == "<New Project>":
                messagebox.showerror("Error", "Please specify a project name.")
                return
            
            # Add script to registry
            success = self.script_registry.add_script(
                file_path,
                language,
                project,
                description,
                dependencies,
                author,
                selected_tags
            )
            
            if success:
                messagebox.showinfo("Success", "Script added to repository successfully!")
                dialog.destroy()
                # Refresh the script list and filters
                self.setup_script_repository_page()
            else:
                messagebox.showerror("Error", "Failed to add script to repository.")
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save",
            height=40,
            fg_color="#28A745",
            hover_color="#218838",
            font=ctk.CTkFont(family="Proxima Nova", size=14, weight="bold"),
            command=save_script
        )
        save_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            height=40,
            fg_color="#6C757D",
            hover_color="#5A6268",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            command=dialog.destroy
        )
        cancel_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
    
    def open_script_inspector(self, script):
        """Open detailed inspector modal for a script"""
        inspector = ctk.CTkToplevel(self)
        inspector.title(f"Script Inspector - {script.get('name', 'Unknown')}")
        inspector.geometry("900x700")
        inspector.transient(self)
        inspector.grab_set()
        
        # Center the inspector
        inspector.update_idletasks()
        x = (inspector.winfo_screenwidth() // 2) - (900 // 2)
        y = (inspector.winfo_screenheight() // 2) - (700 // 2)
        inspector.geometry(f"900x700+{x}+{y}")
        
        # Main container
        container = ctk.CTkFrame(inspector, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        
        # Header with script name
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=script.get("name", "Unknown"),
            font=ctk.CTkFont(family="Proxima Nova", size=20, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Metadata row
        metadata_frame = ctk.CTkFrame(
            container,
            fg_color=("gray95", "#1E1E1E"),
            corner_radius=5
        )
        metadata_frame.grid(row=0, column=0, sticky="ew", pady=(40, 10))
        metadata_frame.grid_columnconfigure(1, weight=1)
        
        # Display metadata
        row = 0
        for label, key in [
            ("Language:", "language"),
            ("Project:", "project"),
            ("Author:", "author"),
            ("Dependencies:", "dependencies"),
            ("Added:", "added_date")
        ]:
            value = script.get(key, "N/A")
            if key == "added_date" and value != "N/A":
                try:
                    dt = datetime.fromisoformat(value)
                    value = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            ctk.CTkLabel(
                metadata_frame,
                text=label,
                font=ctk.CTkFont(family="Proxima Nova", size=12, weight="bold"),
                text_color=("gray30", "gray80")
            ).grid(row=row, column=0, padx=15, pady=5, sticky="w")
            
            ctk.CTkLabel(
                metadata_frame,
                text=value,
                font=ctk.CTkFont(family="Proxima Nova", size=12),
                text_color=("gray10", "gray90")
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            row += 1
        
        # Tags display
        tags = script.get("tags", [])
        if tags:
            ctk.CTkLabel(
                metadata_frame,
                text="Tags:",
                font=ctk.CTkFont(family="Proxima Nova", size=12, weight="bold"),
                text_color=("gray30", "gray80")
            ).grid(row=row, column=0, padx=15, pady=5, sticky="w")
            
            tags_display_frame = ctk.CTkFrame(metadata_frame, fg_color="transparent")
            tags_display_frame.grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            for tag in tags:
                colors = self.TAG_COLORS.get(tag, ("#E0E0E0", "#404040"))
                tag_pill = ctk.CTkLabel(
                    tags_display_frame,
                    text=tag,
                    font=ctk.CTkFont(family="Proxima Nova", size=10),
                    text_color=("gray10", "gray90"),
                    fg_color=colors,
                    corner_radius=10,
                    padx=10,
                    pady=3
                )
                tag_pill.pack(side="left", padx=(0, 5))
        
        # Description section
        if script.get("description"):
            desc_frame = ctk.CTkFrame(
                container,
                fg_color=("white", "#2B2B2B"),
                corner_radius=5,
                border_width=1,
                border_color=("#E0E0E0", "#404040")
            )
            desc_frame.grid(row=1, column=0, sticky="ew", pady=10)
            
            ctk.CTkLabel(
                desc_frame,
                text="Description:",
                font=ctk.CTkFont(family="Proxima Nova", size=12, weight="bold"),
                text_color=("gray30", "gray80")
            ).pack(anchor="w", padx=15, pady=(10, 5))
            
            ctk.CTkLabel(
                desc_frame,
                text=script.get("description", ""),
                font=ctk.CTkFont(family="Proxima Nova", size=12),
                text_color=("gray10", "gray90"),
                wraplength=800,
                justify="left"
            ).pack(anchor="w", padx=15, pady=(0, 10))
        
        # Code preview
        code_frame = ctk.CTkFrame(
            container,
            fg_color=("white", "#2B2B2B"),
            corner_radius=5,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        code_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        code_frame.grid_columnconfigure(0, weight=1)
        code_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(
            code_frame,
            text="Code Preview:",
            font=ctk.CTkFont(family="Proxima Nova", size=12, weight="bold"),
            text_color=("gray30", "gray80")
        ).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
        
        code_textbox = ctk.CTkTextbox(
            code_frame,
            wrap="none",
            font=ctk.CTkFont(family="Courier", size=11),
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#1E1E1E"),
            text_color=("black", "white"),
            border_width=1
        )
        code_textbox.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Load script content
        try:
            script_path = self.script_registry.get_script_absolute_path(script)
            with open(script_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
                code_textbox.insert("0.0", code_content)
        except Exception as e:
            code_textbox.insert("0.0", f"Error loading script: {e}")
        
        code_textbox.configure(state="disabled")  # Make read-only
        
        # Action buttons
        action_frame = ctk.CTkFrame(container, fg_color="transparent")
        action_frame.grid(row=3, column=0, pady=(10, 0), sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)
        action_frame.grid_columnconfigure(2, weight=1)
        
        def run_in_terminal():
            """Run the script in a native terminal window"""
            script_path = self.script_registry.get_script_absolute_path(script)
            language = script.get("language", "")
            
            if not language:
                messagebox.showerror("Error", "Unknown language. Cannot determine how to run this script.")
                return
            
            # Get the command to run
            command = self.script_registry.get_interpreter_command(language, str(script_path))
            
            if not command:
                messagebox.showerror("Error", f"No interpreter configured for {language}")
                return
            
            # Detect OS and open terminal
            system = platform.system()
            
            try:
                if system == "Darwin":  # macOS
                    # Use AppleScript to open Terminal and run command
                    # Use shlex.quote to safely escape the command for AppleScript
                    safe_command = shlex.quote(command)
                    applescript = f'''
                    tell application "Terminal"
                        activate
                        do script {safe_command}
                    end tell
                    '''
                    subprocess.Popen(["osascript", "-e", applescript])
                    
                elif system == "Linux":
                    # Try common Linux terminals with safe command passing
                    # The command is passed to bash -c which handles it safely
                    # We don't quote here because bash -c expects an unquoted command string
                    terminals = [
                        ["gnome-terminal", "--", "bash", "-c", f"{command}; exec bash"],
                        ["xterm", "-e", "bash", "-c", f"{command}; bash"],
                        ["konsole", "-e", "bash", "-c", f"{command}; bash"],
                        ["xfce4-terminal", "-e", "bash", "-c", f"{command}; bash"]
                    ]
                    
                    success = False
                    for term_cmd in terminals:
                        try:
                            subprocess.Popen(term_cmd)
                            success = True
                            break
                        except FileNotFoundError:
                            continue
                    
                    if not success:
                        messagebox.showerror("Error", "Could not find a suitable terminal emulator.")
                        return
                else:
                    messagebox.showerror("Error", f"Terminal launching not supported on {system}")
                    return
                
                messagebox.showinfo("Success", f"Script launched in terminal")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch terminal: {e}")
        
        def open_in_vscode():
            """Open the script in VS Code"""
            script_path = self.script_registry.get_script_absolute_path(script)
            
            try:
                # Try to open in VS Code
                subprocess.Popen(["code", str(script_path)])
                messagebox.showinfo("Success", "Script opened in VS Code")
            except FileNotFoundError:
                messagebox.showerror("Error", "VS Code not found. Please install VS Code or add it to your PATH.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open in VS Code: {e}")
        
        run_btn = ctk.CTkButton(
            action_frame,
            text="Run in Terminal",
            height=40,
            fg_color="#6A5ACD",
            hover_color="#5B4DB8",
            font=ctk.CTkFont(family="Proxima Nova", size=14, weight="bold"),
            command=run_in_terminal
        )
        run_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        vscode_btn = ctk.CTkButton(
            action_frame,
            text="Open in VS Code",
            height=40,
            fg_color="#007ACC",
            hover_color="#005A9E",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            command=open_in_vscode
        )
        vscode_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        close_btn = ctk.CTkButton(
            action_frame,
            text="Close",
            height=40,
            fg_color="#6C757D",
            hover_color="#5A6268",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            command=inspector.destroy
        )
        close_btn.grid(row=0, column=2, padx=(5, 0), sticky="ew")


    def setup_settings_page(self):
        """Setup the settings page"""
        # Save current page values before clearing
        last_page = self.settings_manager.get("last_page", "home")
        if last_page in ["registration", "connectome", "roi", "segmentation"]:
            self._save_page_form_values(last_page)
        
        self.clear_main_pannel()
        self._save_current_page("settings")
        
        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_tools.configure(text="Tools", fg_color="#0078D7")
        
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
        deps_frame.grid(row=2, column=0, pady=20, padx=20, sticky="ew")
        deps_frame.columnconfigure(1, weight=1)
        
        deps_label = ctk.CTkLabel(
            deps_frame,
            text="External Dependencies",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        deps_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="w")
        
        # Check dependency status
        dep_status = self.settings_manager.get_dependency_status()
        
        # Store entry widgets for saving later
        self.dep_path_entries = {}
        
        row_idx = 1
        for dep_name, dep_info in dep_status.items():
            # Dependency name and status on same row
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
            
            row_idx += 1
            
            # Commands list
            commands_text = "Commands: " + ", ".join(dep_info["commands"])
            commands_label = ctk.CTkLabel(
                deps_frame,
                text=commands_text,
                font=ctk.CTkFont(family="Proxima Nova", size=12),
                text_color=("gray40", "gray70")
            )
            commands_label.grid(row=row_idx, column=0, columnspan=3, padx=(40, 20), pady=(0, 5), sticky="w")
            
            row_idx += 1
            
            # Manual path configuration - only show if dependency is not found
            if not dep_info["available"]:
                path_label = ctk.CTkLabel(
                    deps_frame,
                    text="Custom Path:",
                    font=ctk.CTkFont(family="Proxima Nova", size=12),
                    text_color=("gray40", "gray70")
                )
                path_label.grid(row=row_idx, column=0, padx=(40, 10), pady=5, sticky="w")
                
                # Entry for custom path
                path_entry = ctk.CTkEntry(
                    deps_frame,
                    height=30,
                    border_color=("#D0D0D0", "#505050"),
                    fg_color=("white", "#343638"),
                    text_color=("black", "white"),
                    border_width=2
                )
                current_path = dep_info.get("custom_path", "")
                if current_path:
                    path_entry.insert(0, current_path)
                path_entry.grid(row=row_idx, column=1, padx=10, pady=5, sticky="ew")
                
                # Browse button
                browse_btn = ctk.CTkButton(
                    deps_frame,
                    text="...",
                    width=40,
                    height=30,
                    fg_color=("#F0F0F0", "#3A3A3A"),
                    text_color=("black", "white"),
                    hover_color=("#D9D9D9", "#505050"),
                    command=lambda name=dep_name, entry=path_entry: self.browse_dependency_path(name, entry)
                )
                browse_btn.grid(row=row_idx, column=2, padx=(0, 20), pady=5)
                
                # Store entry for later
                self.dep_path_entries[dep_name] = path_entry
                
                row_idx += 1
            else:
                # For available dependencies, store the current custom path (if any) without showing UI
                # This preserves the path information even when dependency is found
                current_path = dep_info.get("custom_path", "")
                if current_path:
                    # Create a hidden entry to preserve the path
                    hidden_entry = ctk.CTkEntry(deps_frame)
                    hidden_entry.insert(0, current_path)
                    self.dep_path_entries[dep_name] = hidden_entry
                    # Don't grid it (keep it hidden)
        
        # Add timestamp of check
        check_time_label = ctk.CTkLabel(
            deps_frame,
            text=f"Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            font=ctk.CTkFont(family="Proxima Nova", size=11, slant="italic"),
            text_color=("gray50", "gray60")
        )
        check_time_label.grid(row=row_idx, column=0, columnspan=3, padx=20, pady=(5, 5), sticky="w")
        row_idx += 1
        
        # Buttons row
        button_frame = ctk.CTkFrame(deps_frame, fg_color="transparent")
        button_frame.grid(row=row_idx, column=0, columnspan=3, pady=(10, 20), padx=20, sticky="ew")
        button_frame.columnconfigure((0, 1), weight=1)
        
        # Save dependencies button
        save_deps_btn = ctk.CTkButton(
            button_frame,
            text="Save Dependency Paths",
            height=35,
            fg_color="#0078D7",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            command=self.save_dependency_paths
        )
        save_deps_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="Refresh Status",
            height=35,
            fg_color="#0078D7",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            command=self.setup_settings_page
        )
        refresh_btn.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        # Appearance Settings Section
        appearance_frame = ctk.CTkFrame(
            self.settings_page,
            fg_color=("white", "#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        appearance_frame.grid(row=1, column=0, pady=20, padx=20, sticky="ew")
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

        # FreeSurfer Configuration Section
        freesurfer_config_frame = ctk.CTkFrame(
            self.settings_page,
            fg_color=("white", "#2B2B2B"),
            corner_radius=10,
            border_width=1,
            border_color=("#E0E0E0", "#404040")
        )
        freesurfer_config_frame.grid(row=3, column=0, pady=20, padx=20, sticky="ew")
        freesurfer_config_frame.columnconfigure(1, weight=1)
        
        freesurfer_config_label = ctk.CTkLabel(
            freesurfer_config_frame,
            text="FreeSurfer Configuration",
            font=ctk.CTkFont(family="Proxima Nova", size=18, weight="bold"),
            text_color=("gray10", "gray90")
        )
        freesurfer_config_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="w")
        
        # FreeSurfer License Path
        license_label = ctk.CTkLabel(
            freesurfer_config_frame,
            text="License File:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        license_label.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="w")
        
        self.freesurfer_license_entry = ctk.CTkEntry(
            freesurfer_config_frame,
            height=35,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        current_license = self.settings_manager.get("external_dependencies.freesurfer_license", "")
        if current_license:
            self.freesurfer_license_entry.insert(0, current_license)
        self.freesurfer_license_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        license_browse_btn = ctk.CTkButton(
            freesurfer_config_frame,
            text="...",
            width=40,
            height=35,
            fg_color=("#F0F0F0", "#3A3A3A"),
            text_color=("black", "white"),
            hover_color=("#D9D9D9", "#505050"),
            command=self.browse_freesurfer_license
        )
        license_browse_btn.grid(row=1, column=2, padx=(0, 20), pady=10)
        
        # FreeSurfer Version for FastSurfer
        fs_version_label = ctk.CTkLabel(
            freesurfer_config_frame,
            text="FreeSurfer for FastSurfer:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        fs_version_label.grid(row=2, column=0, padx=(20, 10), pady=10, sticky="w")
        
        # Detect available FreeSurfer installations
        self.freesurfer_installations = self.settings_manager.detect_freesurfer_installations()
        fs_labels = [label for label, path in self.freesurfer_installations]
        # Add "Custom Path..." option
        fs_labels.append("Custom Path...")
        
        self.freesurfer_version_menu = ctk.CTkOptionMenu(
            freesurfer_config_frame,
            values=fs_labels,
            height=35,
            fg_color=("white", "#343638"),
            button_color=("#0078D7", "#0078D7"),
            button_hover_color=("#005A9E", "#005A9E"),
            dropdown_fg_color=("white", "#2B2B2B"),
            text_color=("black", "white"),
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            command=self.on_freesurfer_version_changed
        )
        
        # Set current value
        current_fs_for_fastsurfer = self.settings_manager.get("external_dependencies.freesurfer_for_fastsurfer", "")
        # Find matching label for current setting
        selected_label = fs_labels[0]  # Default to auto-detected
        for label, path in self.freesurfer_installations:
            if path == current_fs_for_fastsurfer:
                selected_label = label
                break
        # Check if current path is a custom path (not in detected installations)
        if current_fs_for_fastsurfer and selected_label == fs_labels[0] and current_fs_for_fastsurfer != self.freesurfer_installations[0][1]:
            selected_label = "Custom Path..."
        
        self.freesurfer_version_menu.set(selected_label)
        self.freesurfer_version_menu.grid(row=2, column=1, columnspan=2, padx=(10, 20), pady=10, sticky="ew")
        
        # Custom FreeSurfer path entry (initially hidden)
        self.custom_fs_label = ctk.CTkLabel(
            freesurfer_config_frame,
            text="Custom Path:",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            text_color=("gray30", "gray80")
        )
        
        self.custom_fs_entry = ctk.CTkEntry(
            freesurfer_config_frame,
            height=35,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("white", "#343638"),
            text_color=("black", "white"),
            border_width=2
        )
        
        self.custom_fs_browse_btn = ctk.CTkButton(
            freesurfer_config_frame,
            text="...",
            width=40,
            height=35,
            fg_color=("#F0F0F0", "#3A3A3A"),
            text_color=("black", "white"),
            hover_color=("#D9D9D9", "#505050"),
            command=self.browse_custom_freesurfer
        )
        
        # Show custom path entry if "Custom Path..." is selected
        if selected_label == "Custom Path...":
            self.custom_fs_label.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="w")
            if current_fs_for_fastsurfer:
                self.custom_fs_entry.delete(0, ctk.END)  # Clear existing content first
                self.custom_fs_entry.insert(0, current_fs_for_fastsurfer)
            self.custom_fs_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
            self.custom_fs_browse_btn.grid(row=3, column=2, padx=(0, 20), pady=10)
            save_btn_row = 4
        else:
            save_btn_row = 3
        
        # Save FreeSurfer Settings Button
        self.save_fs_settings_btn = ctk.CTkButton(
            freesurfer_config_frame,
            text="Save FreeSurfer Settings",
            height=35,
            fg_color="#0078D7",
            font=ctk.CTkFont(family="Proxima Nova", size=14),
            command=self.save_freesurfer_settings
        )
        self.save_fs_settings_btn.grid(row=save_btn_row, column=0, columnspan=3, pady=(10, 20), padx=20, sticky="ew")


    def setup_history_page(self):
        """Setup the task history page"""
        # Save current page values before clearing
        last_page = self.settings_manager.get("last_page", "home")
        if last_page in ["registration", "connectome", "roi", "segmentation"]:
            self._save_page_form_values(last_page)
        
        self.clear_main_pannel()
        self._save_current_page("history")
        
        # Close tool menu
        self.tools_drawer.grid_forget()
        self.sidebar_btn_tools.configure(text="Tools", fg_color="#0078D7")
        
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
    def browse_file_and_update_subject_id(self, entry_widget, subject_id_widget):
        """Browse for a file and auto-populate subject ID from filename"""
        path = filedialog.askopenfilename()
        if path:
            entry_widget.delete(0, ctk.END)
            entry_widget.insert(0, path)
            # Auto-populate subject ID
            subject_id = XC_SEGMENTATION_TOOLBOX.extract_subject_id_from_filename(path)
            if subject_id:
                subject_id_widget.delete(0, ctk.END)
                subject_id_widget.insert(0, subject_id)
    
    def auto_fill_subject_id(self, input_entry_widget, subject_id_widget):
        """Auto-fill subject ID from the input filename"""
        input_path = input_entry_widget.get().strip()
        if input_path:
            subject_id = XC_SEGMENTATION_TOOLBOX.extract_subject_id_from_filename(input_path)
            if subject_id:
                subject_id_widget.delete(0, ctk.END)
                subject_id_widget.insert(0, subject_id)
            else:
                messagebox.showwarning("Auto-fill", "Could not extract subject ID from filename")
        else:
            messagebox.showwarning("Auto-fill", "Please select an input image first")

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
        
        task = threading.Thread(target=XC_XFM_TOOLBOX.new_xfm, args=(out, fixed, moving_list, self.on_registration_complete, lambda: self.cancel_task_flag), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_registration_complete(self, success=True):
        # Log task completion
        if self.current_task_id is not None:
            status = "completed" if success else "failed"
            self.task_logger.complete_task(self.current_task_id, status)
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        if success:
            self.after(0, self.show_new_registration_complete_message)
        else:
            self.after(0, self.show_new_registration_failed_message)

    def show_new_registration_complete_message(self):
        messagebox.showinfo("Success", "Registration Complete")
    
    def show_new_registration_failed_message(self):
        messagebox.showerror("Error", "Registration failed. Check the console for details.")

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

            task = threading.Thread(target=XC_XFM_TOOLBOX.apply_existing_xfm, args=(out_dir, transform_list, moving_list, reference, self.on_apply_transform_complete, lambda: self.cancel_task_flag), daemon=True)
            self.current_task_thread = task
            task.start()

    def on_apply_transform_complete(self, success=True):
        # Log task completion
        if self.current_task_id is not None:
            status = "completed" if success else "failed"
            self.task_logger.complete_task(self.current_task_id, status)
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        if success:
            self.after(0, self.show_apply_transform_complete_message)
        else:
            self.after(0, self.show_apply_transform_failed_message)
        
    def show_apply_transform_complete_message(self):
        messagebox.showinfo("Success", "Transform Application Complete")
    
    def show_apply_transform_failed_message(self):
        messagebox.showerror("Error", "Transform application failed. Check the console for details.")

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

        task = threading.Thread(target=XC_CONNECTOME_TOOLBOX.gen_connectome, args=(mask_image, tracks_list, output_dir, tracks_weights_list, self.on_connectome_complete, lambda: self.cancel_task_flag), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_connectome_complete(self, success=True):
        # Log task completion
        if self.current_task_id is not None:
            status = "completed" if success else "failed"
            self.task_logger.complete_task(self.current_task_id, status)
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        if success:
            self.after(0, self.show_connectome_complete_message)
        else:
            self.after(0, self.show_connectome_failed_message)

    def show_connectome_complete_message(self):
        messagebox.showinfo("Success", "Connectome Generation Complete")
    
    def show_connectome_failed_message(self):
        messagebox.showerror("Error", "Connectome generation failed. Check the console for details.")

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

        task = threading.Thread(target=XC_CONNECTOME_TOOLBOX.z_scored_connectome, args=(subject_connectome, ref_connectomes_list, output_dir, self.on_z_score_complete, lambda: self.cancel_task_flag), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_z_score_complete(self, success=True):
        # Log task completion
        if self.current_task_id is not None:
            status = "completed" if success else "failed"
            self.task_logger.complete_task(self.current_task_id, status)
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        if success:
            self.after(0, self.show_z_score_complete_message)
        else:
            self.after(0, self.show_z_score_failed_message)

    def show_z_score_complete_message(self):
        messagebox.showinfo("Success", "Z-Score Computation Complete")
    
    def show_z_score_failed_message(self):
        messagebox.showerror("Error", "Z-Score computation failed. Check the console for details.")

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
    
    def on_display_complete(self, success=True):
        # Log task completion
        if self.current_task_id is not None:
            status = "completed" if success else "failed"
            self.task_logger.complete_task(self.current_task_id, status)
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        if success:
            self.after(0, self.show_display_complete_message)
        else:
            self.after(0, self.show_display_failed_message)

    def show_display_complete_message(self):
        messagebox.showinfo("Success", "Connectome Display Complete")
    
    def show_display_failed_message(self):
        messagebox.showerror("Error", "Connectome display failed. Check the console for details.")

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

        task = threading.Thread(target=XC_ROI_TOOLBOX.generate_seeg_roi_masks, args=(ref_mask_img, seeg_coords_file, output_dir, sel_rad, is_bipolar_mode, self.on_seeg_roi_mask_complete, lambda: self.cancel_task_flag), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_seeg_roi_mask_complete(self, success=True):
        # Log task completion
        if self.current_task_id is not None:
            status = "completed" if success else "failed"
            self.task_logger.complete_task(self.current_task_id, status)
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        if success:
            self.after(0, self.show_seeg_roi_mask_complete_message)
        else:
            self.after(0, self.show_seeg_roi_mask_failed_message)

    def show_seeg_roi_mask_complete_message(self):
        messagebox.showinfo("Success", "SEEG ROI Mask Generation Complete")
    
    def show_seeg_roi_mask_failed_message(self):
        messagebox.showerror("Error", "SEEG ROI mask generation failed. Check the console for details.")

## Segmentation Toolbox threading ##

    def start_freeview_thread(self):
        """Start thread to launch freeview"""
        raw_images = self.entry_freeview_images.get("0.0", "end")
        images_list = [line.strip() for line in raw_images.split("\n") if line.strip()]

        # Allow launching without images (user can load manually)
        if not images_list:
            images_list = []
            description = "No images (manual loading)"
        else:
            description = f"{len(images_list)} image(s)"
        
        # Log task start
        self.current_task_id = self.task_logger.start_task(
            "Launch Freeview",
            "Segmentation",
            description,
            input_files=images_list if images_list else [],
            output_location="Display only"
        )
        
        self._show_task_status("Launch Freeview")
        self.cancel_task_flag = False

        task = threading.Thread(target=XC_SEGMENTATION_TOOLBOX.launch_freeview, args=(images_list, None, self.on_freeview_complete, lambda: self.cancel_task_flag), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_freeview_complete(self, success=True):
        # Log task completion
        if self.current_task_id is not None:
            status = "completed" if success else "failed"
            self.task_logger.complete_task(self.current_task_id, status)
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        if success:
            self.after(0, self.show_freeview_complete_message)
        else:
            self.after(0, self.show_freeview_failed_message)

    def show_freeview_complete_message(self):
        messagebox.showinfo("Success", "Freeview launched successfully")
    
    def show_freeview_failed_message(self):
        messagebox.showerror("Error", "Freeview failed to launch. Check the console for details.")

    def start_recon_all_thread(self):
        """Start thread to run FreeSurfer recon-all"""
        input_image = self.entry_recon_input.get().strip()
        subject_id = self.entry_recon_subject_id.get().strip()
        output_dir = self.entry_recon_output.get().strip()

        if not input_image or not subject_id or not output_dir:
            messagebox.showerror("Input Error", "Please provide all required inputs: T1 image, Subject ID, and Output Directory.")
            return
        
        # Get license file from settings
        license_file = self.settings_manager.get("external_dependencies.freesurfer_license", "")
        
        # Log task start
        self.current_task_id = self.task_logger.start_task(
            "FreeSurfer recon-all",
            "Segmentation",
            f"Subject: {subject_id}",
            input_files=[input_image],
            output_location=output_dir
        )
        
        self._show_task_status("FreeSurfer recon-all")
        self.cancel_task_flag = False

        task = threading.Thread(target=XC_SEGMENTATION_TOOLBOX.run_recon_all, args=(input_image, subject_id, output_dir, license_file, None, self.on_recon_all_complete, lambda: self.cancel_task_flag), daemon=True)
        self.current_task_thread = task
        task.start()

    def on_recon_all_complete(self, success=True):
        # Log task completion
        if self.current_task_id is not None:
            status = "completed" if success else "failed"
            self.task_logger.complete_task(self.current_task_id, status)
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        if success:
            self.after(0, self.show_recon_all_complete_message)
        else:
            self.after(0, self.show_recon_all_failed_message)

    def show_recon_all_complete_message(self):
        messagebox.showinfo("Success", "FreeSurfer recon-all completed")
    
    def show_recon_all_failed_message(self):
        messagebox.showerror("Error", "FreeSurfer recon-all failed. Check the console for details.")

    def start_fastsurfer_thread(self):
        """Start thread to run FastSurfer"""
        input_image = self.entry_fastsurfer_input.get().strip()
        subject_id = self.entry_fastsurfer_subject_id.get().strip()
        output_dir = self.entry_fastsurfer_output.get().strip()

        if not input_image or not subject_id or not output_dir:
            messagebox.showerror("Input Error", "Please provide all required inputs: T1 image, Subject ID, and Output Directory.")
            return
        
        # Get GPU toggle state
        use_gpu = self.fastsurfer_gpu_toggle.get() == 1
        
        # Get paths from settings
        license_file = self.settings_manager.get("external_dependencies.freesurfer_license", "")
        fastsurfer_home = self.settings_manager.get("external_dependencies.fastsurfer_home", "")
        freesurfer_for_fastsurfer = self.settings_manager.get("external_dependencies.freesurfer_for_fastsurfer", "")
        
        # Log task start
        self.current_task_id = self.task_logger.start_task(
            "FastSurfer",
            "Segmentation",
            f"Subject: {subject_id}",
            input_files=[input_image],
            output_location=output_dir
        )
        
        self._show_task_status("FastSurfer")
        self.cancel_task_flag = False

        task = threading.Thread(
            target=XC_SEGMENTATION_TOOLBOX.run_fastsurfer,
            args=(
                input_image,
                subject_id,
                output_dir,
                fastsurfer_home,
                license_file,
                use_gpu,
                None,  # num_threads
                freesurfer_for_fastsurfer,
                self.on_fastsurfer_complete,
                lambda: self.cancel_task_flag
            ),
            daemon=True
        )
        self.current_task_thread = task
        task.start()

    def on_fastsurfer_complete(self, success=True):
        # Log task completion
        if self.current_task_id is not None:
            status = "completed" if success else "failed"
            self.task_logger.complete_task(self.current_task_id, status)
            self.current_task_id = None
        self.current_task_thread = None
        self._hide_task_status()
        if success:
            self.after(0, self.show_fastsurfer_complete_message)
        else:
            self.after(0, self.show_fastsurfer_failed_message)

    def show_fastsurfer_complete_message(self):
        messagebox.showinfo("Success", "FastSurfer completed")
    
    def show_fastsurfer_failed_message(self):
        messagebox.showerror("Error", "FastSurfer failed. Check the console for details.")

    def browse_freesurfer_license(self):
        """Browse for FreeSurfer license file"""
        path = filedialog.askopenfilename(title="Select FreeSurfer License File", filetypes=[("License files", "*.txt"), ("All files", "*.*")])
        if path:
            self.freesurfer_license_entry.delete(0, ctk.END)
            self.freesurfer_license_entry.insert(0, path)
    
    def on_freesurfer_version_changed(self, selected_value):
        """Handle FreeSurfer version dropdown change"""
        if selected_value == "Custom Path...":
            # Show custom path entry
            self.custom_fs_label.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="w")
            self.custom_fs_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
            self.custom_fs_browse_btn.grid(row=3, column=2, padx=(0, 20), pady=10)
            # Move save button to row 4
            self.save_fs_settings_btn.grid(row=4, column=0, columnspan=3, pady=(10, 20), padx=20, sticky="ew")
        else:
            # Hide custom path entry
            self.custom_fs_label.grid_forget()
            self.custom_fs_entry.grid_forget()
            self.custom_fs_browse_btn.grid_forget()
            # Move save button back to row 3
            self.save_fs_settings_btn.grid(row=3, column=0, columnspan=3, pady=(10, 20), padx=20, sticky="ew")
    
    def browse_custom_freesurfer(self):
        """Browse for custom FreeSurfer installation directory"""
        path = filedialog.askdirectory(title="Select FreeSurfer Installation Directory")
        if path:
            self.custom_fs_entry.delete(0, ctk.END)
            self.custom_fs_entry.insert(0, path)
    
    def save_freesurfer_settings(self):
        """Save FreeSurfer configuration settings"""
        license_path = self.freesurfer_license_entry.get().strip()
        self.settings_manager.set("external_dependencies.freesurfer_license", license_path)
        
        # Save FreeSurfer version selection for FastSurfer
        selected_label = self.freesurfer_version_menu.get()
        
        if selected_label == "Custom Path...":
            # Use custom path from entry
            selected_path = self.custom_fs_entry.get().strip()
        else:
            # Find the path corresponding to the selected label
            selected_path = ""
            for label, path in self.freesurfer_installations:
                if label == selected_label:
                    selected_path = path
                    break
        
        self.settings_manager.set("external_dependencies.freesurfer_for_fastsurfer", selected_path)
        
        messagebox.showinfo("Success", "FreeSurfer settings saved successfully")
    
    def browse_dependency_path(self, dep_name, entry_widget):
        """Browse for dependency installation directory"""
        path = filedialog.askdirectory(title=f"Select {dep_name} Installation Directory")
        if path:
            entry_widget.delete(0, ctk.END)
            entry_widget.insert(0, path)
    
    def save_dependency_paths(self):
        """Save custom dependency paths and set up environment"""
        # Mapping of dependency names to setting keys
        dep_mapping = {
            "ANTs": "ants_path",
            "MRtrix3": "mrtrix_path",
            "FreeSurfer": "freesurfer_home",
            "FastSurfer": "fastsurfer_home"
        }
        
        saved_count = 0
        errors = []
        
        for dep_name, entry_widget in self.dep_path_entries.items():
            path = entry_widget.get().strip()
            setting_key = dep_mapping.get(dep_name)
            
            if not setting_key:
                continue
            
            # Save the path
            self.settings_manager.set(f"external_dependencies.{setting_key}", path)
            
            if path:
                # Validate the path exists
                if not os.path.exists(path):
                    errors.append(f"{dep_name}: Path does not exist")
                    continue
                
                # Try to set up the dependency environment
                success = self._setup_dependency_environment(dep_name, path)
                if success:
                    saved_count += 1
                else:
                    errors.append(f"{dep_name}: Could not verify installation")
        
        # Show result message
        if errors:
            error_msg = "Some dependencies could not be configured:\n" + "\n".join(errors)
            if saved_count > 0:
                error_msg = f"Saved {saved_count} dependency path(s).\n\n" + error_msg
            messagebox.showwarning("Partial Success", error_msg)
        else:
            messagebox.showinfo("Success", f"All dependency paths saved successfully!\n\nPlease refresh to see updated status.")
    
    def _setup_dependency_environment(self, dep_name, path):
        """
        Attempt to set up environment for a dependency.
        Returns True if successful, False otherwise.
        """
        try:
            if dep_name == "ANTs":
                # Check for ANTs bin directory
                bin_path = os.path.join(path, "bin")
                if os.path.exists(bin_path):
                    # Add to PATH in current environment
                    current_path = os.environ.get("PATH", "")
                    if bin_path not in current_path:
                        os.environ["PATH"] = bin_path + os.pathsep + current_path
                    return True
                # If no bin directory, assume path is the bin directory itself
                elif any(os.path.exists(os.path.join(path, cmd)) for cmd in ["antsRegistrationSyN.sh", "antsApplyTransforms"]):
                    current_path = os.environ.get("PATH", "")
                    if path not in current_path:
                        os.environ["PATH"] = path + os.pathsep + current_path
                    return True
                return False
            
            elif dep_name == "MRtrix3":
                # Check for MRtrix3 bin directory
                bin_path = os.path.join(path, "bin")
                if os.path.exists(bin_path):
                    current_path = os.environ.get("PATH", "")
                    if bin_path not in current_path:
                        os.environ["PATH"] = bin_path + os.pathsep + current_path
                    return True
                elif os.path.exists(os.path.join(path, "tck2connectome")):
                    current_path = os.environ.get("PATH", "")
                    if path not in current_path:
                        os.environ["PATH"] = path + os.pathsep + current_path
                    return True
                return False
            
            elif dep_name == "FreeSurfer":
                # Check for FreeSurfer installation
                setup_script = os.path.join(path, "SetUpFreeSurfer.sh")
                bin_path = os.path.join(path, "bin")
                if os.path.exists(setup_script) or os.path.exists(bin_path):
                    os.environ["FREESURFER_HOME"] = path
                    if os.path.exists(bin_path):
                        current_path = os.environ.get("PATH", "")
                        if bin_path not in current_path:
                            os.environ["PATH"] = bin_path + os.pathsep + current_path
                    return True
                return False
            
            elif dep_name == "FastSurfer":
                # Check for FastSurfer installation
                run_script = os.path.join(path, "run_fastsurfer.sh")
                if os.path.exists(run_script):
                    os.environ["FASTSURFER_HOME"] = path
                    return True
                return False
            
            return False
        except Exception as e:
            print(f"Error setting up {dep_name}: {e}")
            return False


# MAIN LOOP #        
if __name__ == "__main__":
    app = CLAP()
    app.mainloop()