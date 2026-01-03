import json
import os
import shutil
import shlex
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ScriptRegistry:
    """Manages the script registry for CLAP"""
    
    # Language to file extension mapping
    LANGUAGE_EXTENSIONS = {
        '.py': 'Python',
        '.sh': 'Bash',
        '.R': 'R',
        '.r': 'R',
        '.m': 'Matlab',
        '.js': 'JavaScript',
        '.pl': 'Perl',
        '.rb': 'Ruby'
    }
    
    # Extension to interpreter command mapping
    # Note: Matlab is special-cased in get_interpreter_command()
    LANGUAGE_INTERPRETERS = {
        'Python': 'python',
        'Bash': 'bash',
        'R': 'Rscript',
        'Matlab': 'matlab',
        'JavaScript': 'node',
        'Perl': 'perl',
        'Ruby': 'ruby'
    }
    
    # Tag options with their colors
    TAG_OPTIONS = {
        'analysis': '#28A745',      # Green
        'statistics': '#007BFF',    # Blue
        'setup': '#DC3545',         # Red
        'other': '#6F42C1'          # Purple
    }
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.registry_file = self.base_path / "registry.json"
        self.registry_dir = self.base_path / "registry"
        
        # Ensure directories and files exist
        self._ensure_registry_structure()
        
        # Load registry
        self.registry_data = self._load_registry()
    
    def _ensure_registry_structure(self):
        """Create registry directory and file if they don't exist"""
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.registry_file.exists():
            self._save_registry({"scripts": []})
    
    def _load_registry(self) -> Dict:
        """Load registry from JSON file"""
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading registry: {e}. Creating new registry.")
            return {"scripts": []}
    
    def _save_registry(self, data: Dict):
        """Save registry to JSON file"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            print(f"Error saving registry: {e}")
    
    def detect_language(self, file_path: str) -> str:
        """Detect language from file extension"""
        ext = Path(file_path).suffix.lower()
        return self.LANGUAGE_EXTENSIONS.get(ext, "Unknown")
    
    def extract_description_from_file(self, file_path: str) -> str:
        """
        Try to extract description from file comments.
        Looks for comment blocks at the beginning of the file.
        
        Args:
            file_path: Path to the script file
            
        Returns:
            String containing the extracted description (max 200 chars).
            Returns empty string if no description found or error occurs.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # Skip empty lines at the beginning
                start_idx = 0
                while start_idx < len(lines) and not lines[start_idx].strip():
                    start_idx += 1
                
                if start_idx >= len(lines):
                    return ""
                
                # Detect comment style based on first non-empty line
                first_line = lines[start_idx].strip()
                description_lines = []
                
                # Python/Bash style (#)
                if first_line.startswith('#'):
                    for line in lines[start_idx:]:
                        stripped = line.strip()
                        if stripped.startswith('#'):
                            # Remove # and shebang lines
                            if not stripped.startswith('#!'):
                                desc = stripped.lstrip('#').strip()
                                if desc:
                                    description_lines.append(desc)
                        elif stripped:
                            break  # Stop at first non-comment line
                
                # Multi-line comments (/* */ or """)
                elif first_line.startswith('"""') or first_line.startswith("'''"):
                    in_docstring = True
                    quote = '"""' if '"""' in first_line else "'''"
                    # Check if docstring ends on same line
                    if first_line.count(quote) >= 2:
                        desc = first_line.replace(quote, '').strip()
                        if desc:
                            description_lines.append(desc)
                    else:
                        for line in lines[start_idx + 1:]:
                            if quote in line:
                                desc = line.split(quote)[0].strip()
                                if desc:
                                    description_lines.append(desc)
                                break
                            else:
                                desc = line.strip()
                                if desc:
                                    description_lines.append(desc)
                
                # Return first few lines as description (max 200 chars)
                if description_lines:
                    full_desc = ' '.join(description_lines)
                    return full_desc[:200] if len(full_desc) > 200 else full_desc
                
        except Exception as e:
            print(f"Error extracting description: {e}")
        
        return ""
    
    def add_script(
        self,
        source_file_path: str,
        language: str,
        project: str,
        description: str,
        dependencies: str,
        author: str,
        tags: List[str] = None
    ) -> bool:
        """
        Add a new script to the registry.
        
        Args:
            source_file_path: Path to the source script file
            language: Programming language (required, non-empty)
            project: Project name/category (required, non-empty)
            description: Script description
            dependencies: Required dependencies
            author: Script author
            tags: List of tags (e.g., ['analysis', 'statistics'])
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not source_file_path or not source_file_path.strip():
                print("Error: Source file path is required")
                return False
            
            if not language or not language.strip():
                print("Error: Language is required")
                return False
            
            if not project or not project.strip():
                print("Error: Project name is required")
                return False
            
            source_path = Path(source_file_path)
            
            if not source_path.exists():
                print(f"Error: Source file does not exist: {source_file_path}")
                return False
            
            # Generate unique filename if file already exists
            dest_filename = source_path.name
            dest_path = self.registry_dir / dest_filename
            
            counter = 1
            while dest_path.exists():
                name_parts = source_path.stem
                ext = source_path.suffix
                dest_filename = f"{name_parts}_{counter}{ext}"
                dest_path = self.registry_dir / dest_filename
                counter += 1
            
            # Copy file to registry directory
            shutil.copy2(source_path, dest_path)
            
            # Create registry entry
            script_entry = {
                "filename": dest_filename,
                "name": source_path.stem,
                "language": language,
                "project": project,
                "description": description,
                "dependencies": dependencies,
                "author": author,
                "tags": tags if tags else [],
                "added_date": datetime.now().isoformat(),
                "relative_path": f"registry/{dest_filename}"
            }
            
            # Add to registry
            self.registry_data["scripts"].append(script_entry)
            self._save_registry(self.registry_data)
            
            return True
            
        except Exception as e:
            print(f"Error adding script to registry: {e}")
            return False
    
    def get_all_scripts(self) -> List[Dict]:
        """Get all scripts from registry"""
        return self.registry_data.get("scripts", [])
    
    def get_script_by_filename(self, filename: str) -> Optional[Dict]:
        """Get a specific script by filename"""
        for script in self.registry_data.get("scripts", []):
            if script["filename"] == filename:
                return script
        return None
    
    def filter_scripts(
        self,
        project: Optional[str] = None,
        language: Optional[str] = None,
        author: Optional[str] = None,
        tag: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[Dict]:
        """
        Filter scripts based on criteria
        
        Args:
            project: Filter by project name
            language: Filter by language
            author: Filter by author
            tag: Filter by tag
            search_term: Search in name and description
            
        Returns:
            List of matching scripts
        """
        scripts = self.get_all_scripts()
        
        if project:
            scripts = [s for s in scripts if s.get("project", "").lower() == project.lower()]
        
        if language:
            scripts = [s for s in scripts if s.get("language", "").lower() == language.lower()]
        
        if author:
            scripts = [s for s in scripts if s.get("author", "").lower() == author.lower()]
        
        if tag:
            scripts = [s for s in scripts if tag in (s.get("tags") or [])]
        
        if search_term:
            term = search_term.lower()
            scripts = [
                s for s in scripts
                if term in s.get("name", "").lower() or term in s.get("description", "").lower()
            ]
        
        return scripts
    
    def get_unique_projects(self) -> List[str]:
        """Get list of unique project names"""
        projects = set()
        for script in self.get_all_scripts():
            project = script.get("project", "")
            if project:
                projects.add(project)
        return sorted(list(projects))
    
    def get_unique_languages(self) -> List[str]:
        """Get list of unique languages"""
        languages = set()
        for script in self.get_all_scripts():
            language = script.get("language", "")
            if language:
                languages.add(language)
        return sorted(list(languages))
    
    def get_unique_authors(self) -> List[str]:
        """Get list of unique authors"""
        authors = set()
        for script in self.get_all_scripts():
            author = script.get("author", "")
            if author:
                authors.add(author)
        return sorted(list(authors))
    
    def get_unique_tags(self) -> List[str]:
        """Get list of unique tags from all scripts"""
        tags = set()
        for script in self.get_all_scripts():
            script_tags = script.get("tags") or []
            if script_tags:
                tags.update(script_tags)
        return sorted(list(tags))
    
    def get_script_absolute_path(self, script: Dict) -> Path:
        """Get absolute path to a script file"""
        return self.base_path / script["relative_path"]
    
    def get_interpreter_command(self, language: str, script_path: str) -> str:
        """
        Get the command to execute a script with proper shell escaping
        
        This returns a command string that is safe to pass to bash -c or similar.
        The script path is properly escaped using shlex.quote.
        
        Args:
            language: Programming language
            script_path: Absolute path to script file
            
        Returns:
            Command string to execute the script (safely quoted for shell execution)
        """
        interpreter = self.LANGUAGE_INTERPRETERS.get(language, "")
        
        if not interpreter:
            return ""
        
        # Use shlex.quote to safely escape the script path for shell execution
        safe_path = shlex.quote(script_path)
        
        # Special handling for Matlab
        if language == "Matlab":
            # Matlab -batch expects a Matlab command as a string argument
            # We escape single quotes for Matlab, and the whole thing is safe for shell
            matlab_safe = script_path.replace("'", "''")  # Matlab string escaping
            # The double quotes around the batch argument protect it from shell expansion
            return f"{interpreter} -batch \"run('{matlab_safe}')\""
        
        # For all other languages, use interpreter with properly quoted path
        return f"{interpreter} {safe_path}"
    
    def delete_script(self, filename: str) -> bool:
        """
        Delete a script from the registry and filesystem
        
        Args:
            filename: Name of the script file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find and remove from registry
            scripts = self.registry_data.get("scripts", [])
            script_to_delete = None
            
            for i, script in enumerate(scripts):
                if script["filename"] == filename:
                    script_to_delete = scripts.pop(i)
                    break
            
            if script_to_delete:
                # Delete file from filesystem
                file_path = self.base_path / script_to_delete["relative_path"]
                if file_path.exists():
                    file_path.unlink()
                
                # Save updated registry
                self._save_registry(self.registry_data)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting script: {e}")
            return False
