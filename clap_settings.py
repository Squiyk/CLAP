import json
import os
from pathlib import Path
import shutil
import re

class SettingsManager:
    """Manages user settings and configuration for CLAP application"""
    
    # FreeSurfer version detection ranges
    FREESURFER_MIN_VERSION = 6  # Minimum major version to search for
    FREESURFER_MAX_VERSION = 9  # Maximum major version to search for
    FREESURFER_MAX_MINOR = 10    # Maximum minor version to search for
    
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
                "mrtrix_path": "",
                "freesurfer_home": "",
                "freesurfer_license": "",
                "fastsurfer_home": "",
                "freesurfer_for_fastsurfer": ""  # FreeSurfer version to use specifically for FastSurfer
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
                    # Deep merge loaded settings with defaults to ensure all keys exist
                    # This preserves new keys added to default_settings in updates
                    settings = self._deep_merge(self.default_settings.copy(), loaded)
                    return settings
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}. Using defaults.")
                return self.default_settings.copy()
        else:
            return self.default_settings.copy()
    
    def _deep_merge(self, base, overlay):
        """
        Recursively merge overlay dict into base dict.
        Preserves keys in base that don't exist in overlay.
        """
        import copy
        result = copy.deepcopy(base)
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
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
        ants_custom_path = self.get("external_dependencies.ants_path", "")
        ants_available = all(self.check_dependency(cmd) for cmd in ants_commands)
        
        # If not in PATH, check custom path
        if not ants_available and ants_custom_path:
            ants_available = self._check_commands_in_path(ants_commands, ants_custom_path)
        
        status["ANTs"] = {
            "available": ants_available,
            "commands": ants_commands,
            "custom_path": ants_custom_path
        }
        
        # Check MRtrix3 commands
        mrtrix_commands = ["tck2connectome"]
        mrtrix_custom_path = self.get("external_dependencies.mrtrix_path", "")
        mrtrix_available = all(self.check_dependency(cmd) for cmd in mrtrix_commands)
        
        if not mrtrix_available and mrtrix_custom_path:
            mrtrix_available = self._check_commands_in_path(mrtrix_commands, mrtrix_custom_path)
        
        status["MRtrix3"] = {
            "available": mrtrix_available,
            "commands": mrtrix_commands,
            "custom_path": mrtrix_custom_path
        }
        
        # Check FreeSurfer commands
        freesurfer_commands = ["recon-all", "freeview"]
        freesurfer_custom_path = self.get("external_dependencies.freesurfer_home", "")
        freesurfer_available = all(self.check_dependency(cmd) for cmd in freesurfer_commands)
        
        if not freesurfer_available and freesurfer_custom_path:
            freesurfer_available = self._check_commands_in_path(freesurfer_commands, freesurfer_custom_path)
        
        status["FreeSurfer"] = {
            "available": freesurfer_available,
            "commands": freesurfer_commands,
            "custom_path": freesurfer_custom_path,
            "license_path": self.get("external_dependencies.freesurfer_license", "")
        }
        
        # Check FastSurfer (run_fastsurfer.sh)
        fastsurfer_commands = ["run_fastsurfer.sh"]
        fastsurfer_custom_path = self.get("external_dependencies.fastsurfer_home", "")
        fastsurfer_available = self.check_dependency("run_fastsurfer.sh")
        
        if not fastsurfer_available and fastsurfer_custom_path:
            fastsurfer_available = self._check_commands_in_path(fastsurfer_commands, fastsurfer_custom_path)
        
        status["FastSurfer"] = {
            "available": fastsurfer_available,
            "commands": fastsurfer_commands,
            "custom_path": fastsurfer_custom_path
        }
        
        return status
    
    def _check_commands_in_path(self, commands, base_path):
        """
        Check if commands exist in a custom path.
        Checks both the base path and base_path/bin directory.
        """
        if not base_path or not os.path.exists(base_path):
            return False
        
        # Check in base path
        for cmd in commands:
            cmd_path = os.path.join(base_path, cmd)
            if os.path.exists(cmd_path) and os.access(cmd_path, os.X_OK):
                continue
            
            # Check in bin subdirectory
            bin_path = os.path.join(base_path, "bin", cmd)
            if os.path.exists(bin_path) and os.access(bin_path, os.X_OK):
                continue
            
            # Command not found
            return False
        
        return True
    
    def detect_freesurfer_installations(self):
        """
        Detect available FreeSurfer installations on the system.
        Returns a list of tuples: (label, path) where label is a display name and path is FREESURFER_HOME.
        The first entry is always the auto-detected version from the environment.
        """
        installations = []
        
        # Check for FreeSurfer in environment
        env_freesurfer = os.environ.get('FREESURFER_HOME', '')
        if env_freesurfer and os.path.exists(env_freesurfer):
            # Try to get version
            version = self._get_freesurfer_version(env_freesurfer)
            if version:
                installations.append((f"Auto-detected ({version})", env_freesurfer))
            else:
                installations.append(("Auto-detected", env_freesurfer))
        else:
            # No FreeSurfer in environment
            installations.append(("Auto-detected (None)", ""))
        
        # Check common installation paths
        common_paths = [
            "/usr/local/freesurfer",
            "/Applications/freesurfer",
            os.path.expanduser("~/freesurfer"),
            "/opt/freesurfer"
        ]
        
        # Also check versioned paths
        for major_version in range(self.FREESURFER_MIN_VERSION, self.FREESURFER_MAX_VERSION + 1):
            for minor_version in range(0, self.FREESURFER_MAX_MINOR):
                common_paths.append(f"/usr/local/freesurfer/{major_version}.{minor_version}")
                common_paths.append(f"/Applications/freesurfer/{major_version}.{minor_version}")
                common_paths.append(os.path.expanduser(f"~/freesurfer/{major_version}.{minor_version}"))
                common_paths.append(f"/opt/freesurfer-{major_version}.{minor_version}")
        
        # Check each path
        seen_paths = {env_freesurfer} if env_freesurfer else set()
        for path in common_paths:
            if path and os.path.exists(path) and path not in seen_paths:
                # Verify it's actually FreeSurfer by checking for key files
                if self._is_valid_freesurfer_installation(path):
                    version = self._get_freesurfer_version(path)
                    if version:
                        installations.append((f"FreeSurfer {version} ({path})", path))
                    else:
                        installations.append((f"FreeSurfer ({path})", path))
                    seen_paths.add(path)
        
        return installations
    
    def _is_valid_freesurfer_installation(self, path):
        """Check if a path contains a valid FreeSurfer installation"""
        # Check for key FreeSurfer files/directories
        key_paths = [
            os.path.join(path, "bin", "recon-all"),
            os.path.join(path, "bin", "mri_convert"),
            os.path.join(path, "SetUpFreeSurfer.sh")
        ]
        return any(os.path.exists(p) for p in key_paths)
    
    def _get_freesurfer_version(self, freesurfer_home):
        """
        Try to detect FreeSurfer version from the installation.
        Returns version string (major.minor) or None if not found.
        """
        # Try to read version from build-stamp.txt
        build_stamp = os.path.join(freesurfer_home, "build-stamp.txt")
        if os.path.exists(build_stamp):
            try:
                with open(build_stamp, 'r') as f:
                    content = f.read().strip()
                    # Look for standalone version segment (pure digits and dots only)
                    # This avoids matching OS versions like "centos7.5" or "ubuntu22.04"
                    if '-' in content:
                        parts = content.split('-')
                        for part in parts:
                            # Check if this part is a pure version number (only digits and dots)
                            if re.match(r'^\d+\.\d+(?:\.\d+)?$', part.strip()):
                                version_parts = part.split('.')
                                # Return major.minor only (guaranteed to have at least 2 parts by regex)
                                return version_parts[0] + '.' + version_parts[1]
            except Exception:
                pass
        
        # Try alternate approach: check directory name
        # Validate against FREESURFER_MIN_VERSION and FREESURFER_MAX_VERSION
        dir_name = os.path.basename(freesurfer_home.rstrip('/'))
        # Use word boundary pattern (unlike build-stamp which uses strict anchors)
        # since directory names may contain version as part of a longer string
        match = re.search(r'\b(\d+\.\d+)(?:\.\d+)?\b', dir_name)
        if match:
            version = match.group(1)
            # Validate major version is in expected range
            major_version = int(version.split('.')[0])
            if self.FREESURFER_MIN_VERSION <= major_version <= self.FREESURFER_MAX_VERSION:
                return version
        
        return None
