import json
from pathlib import Path
from datetime import datetime

class TaskLogger:
    """Manages task history logging for CLAP application"""
    
    def __init__(self):
        self.user_data_dir = Path(__file__).parent / "user_data"
        self.log_file = self.user_data_dir / "task_history.json"
        self.text_log_file = self.user_data_dir / "task_history.log"
        self._ensure_user_data_dir()
        self.tasks = self._load_tasks()
        # Use persistent counter for unique IDs
        self.next_task_id = max([t.get("id", -1) for t in self.tasks], default=-1) + 1
    
    def _ensure_user_data_dir(self):
        """Create user_data directory if it doesn't exist"""
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_tasks(self):
        """Load task history from file"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading task history: {e}")
                return []
        return []
    
    def _save_tasks(self):
        """Save task history to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.tasks, f, indent=4)
        except IOError as e:
            print(f"Error saving task history: {e}")
    
    def _append_to_text_log(self, message):
        """Append a message to the human-readable text log"""
        try:
            with open(self.text_log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except IOError as e:
            print(f"Error writing to text log: {e}")
    
    def start_task(self, task_name, task_type, details="", input_files=None, output_location=""):
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
        
        # Write to text log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] STARTED - ID: {self.next_task_id} | {task_type}: {task_name}"
        if details:
            log_message += f" | Details: {details}"
        if input_files:
            log_message += f" | Input files: {len(input_files)} file(s)"
        if output_location:
            log_message += f" | Output: {output_location}"
        self._append_to_text_log(log_message)
        
        task_id = self.next_task_id
        self.next_task_id += 1
        return task_id
    
    def complete_task(self, task_id, status="completed", error_message=""):
        """Log the completion of a task"""
        # Find task by ID
        for task in self.tasks:
            if task.get("id") == task_id:
                end_time = datetime.now()
                task["end_time"] = end_time.isoformat()
                task["status"] = status
                task["error_message"] = error_message
                self._save_tasks()
                
                # Write to text log
                timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
                start_time = datetime.fromisoformat(task["start_time"])
                duration = (end_time - start_time).total_seconds()
                
                status_upper = status.upper()
                log_message = f"[{timestamp}] {status_upper} - ID: {task_id} | {task['type']}: {task['name']} | Duration: {duration:.1f}s"
                if error_message:
                    log_message += f" | Error: {error_message}"
                self._append_to_text_log(log_message)
                return
        # If task not found, log a warning
        print(f"Warning: Task ID {task_id} not found in task history")
    
    def get_recent_tasks(self, limit=50):
        """Get recent tasks in reverse chronological order"""
        return list(reversed(self.tasks[-limit:]))
    
    def get_all_tasks(self):
        """Get all tasks in reverse chronological order"""
        return list(reversed(self.tasks))
    
    def clear_history(self):
        """Clear all task history"""
        self.tasks = []
        self._save_tasks()
        # Add a separator in the text log to indicate history was cleared
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._append_to_text_log(f"\n{'='*80}")
        self._append_to_text_log(f"[{timestamp}] HISTORY CLEARED")
        self._append_to_text_log(f"{'='*80}\n")
