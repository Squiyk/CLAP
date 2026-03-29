import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

class TaskLogger:
    """Manages task history logging for CLAP application"""
    
    def __init__(self) -> None:
        self.user_data_dir = Path(__file__).parent / "user_data"
        self.log_file = self.user_data_dir / "task_history.json"
        self._ensure_user_data_dir()
        self.tasks = self._load_tasks()
        # Use persistent counter for unique IDs
        self.next_task_id = max([t.get("id", -1) for t in self.tasks], default=-1) + 1
    
    def _ensure_user_data_dir(self) -> None:
        """Create user_data directory if it doesn't exist"""
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_tasks(self) -> List[Dict[str, Any]]:
        """Load task history from file"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading task history: {e}")
                return []
        return []
    
    def _save_tasks(self) -> None:
        """Save task history to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.tasks, f, indent=4)
        except IOError as e:
            print(f"Error saving task history: {e}")
    
    def start_task(
        self,
        task_name: str,
        task_type: str,
        details: str = "",
        input_files: Optional[List[str]] = None,
        output_location: str = ""
    ) -> int:
        """Log the start of a task"""
        task_entry = {
            "id": self.next_task_id,
            "name": task_name,
            "type": task_type,
            "details": details,
            "input_files": input_files if input_files else [],
            "output_location": output_location,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "error_message": ""
        }
        self.tasks.append(task_entry)
        self._save_tasks()
        task_id = self.next_task_id
        self.next_task_id += 1
        return task_id
    
    def complete_task(self, task_id: int, status: str = "completed", error_message: str = "") -> None:
        """Log the completion of a task"""
        # Find task by ID
        for task in self.tasks:
            if task.get("id") == task_id:
                task["end_time"] = datetime.now().isoformat()
                task["status"] = status
                task["error_message"] = error_message
                self._save_tasks()
                return
        # If task not found, log a warning
        print(f"Warning: Task ID {task_id} not found in task history")
    
    def get_recent_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent tasks in reverse chronological order"""
        return list(reversed(self.tasks[-limit:]))
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks in reverse chronological order"""
        return list(reversed(self.tasks))
    
    def clear_history(self) -> None:
        """Clear all task history"""
        self.tasks = []
        self._save_tasks()
