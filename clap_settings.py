import json
import os
from pathlib import Path
import shutil

class SettingsManager:
    """Manages user settings and configuration for CLAP application"""
    
    def __init__(self):
        self.user_data_dir = Path(__file__).parent / "user_data"
        self.settings_file = self.user_data_dir / "settings.json"
        self.default_settings = {
            "appearance_mode": "System",
            "color_theme": "blue",
            "last_page": "home",
            "tools_menu_expanded": False,
            "external_dependencies": {
                "ants_path": "",
                "mrtrix_path": ""
            }
        }
        self._ensure_user_data_dir()
        self.settings = self._load_settings()
    
    def _ensure_user_data_dir(self):
        """Create user_data directory if it doesn't exist"""
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_settings(self):
        """Load settings from file or create default settings"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}. Using defaults.")
                return self.default_settings.copy()
        else:
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key, default=None):
        """Get a setting value"""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key, value):
        """Set a setting value"""
        keys = key.split('.')
        settings = self.settings
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        settings[keys[-1]] = value
        self.save_settings()
    
    def check_dependency(self, command):
        """Check if an external dependency is available in PATH"""
        return shutil.which(command) is not None
    
    def get_dependency_status(self):
        """Check status of all external dependencies"""
        status = {}
        
        # Check ANTs commands
        ants_commands = ["antsRegistrationSyN.sh", "antsApplyTransforms"]
        ants_available = all(self.check_dependency(cmd) for cmd in ants_commands)
        status["ANTs"] = {
            "available": ants_available,
            "commands": ants_commands,
            "custom_path": self.get("external_dependencies.ants_path", "")
        }
        
        # Check MRtrix3 commands
        mrtrix_commands = ["tck2connectome"]
        mrtrix_available = all(self.check_dependency(cmd) for cmd in mrtrix_commands)
        status["MRtrix3"] = {
            "available": mrtrix_available,
            "commands": mrtrix_commands,
            "custom_path": self.get("external_dependencies.mrtrix_path", "")
        }
        
        return status
