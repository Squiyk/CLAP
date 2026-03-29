"""Subprocess utility functions for CLAP application."""
import subprocess
from typing import Optional, Callable, List
from utils.constants import PROCESS_TERMINATION_TIMEOUT


def run_cancellable_process(
    cmd: List[str],
    on_complete: Optional[Callable[[bool], None]] = None,
    cancel_checker: Optional[Callable[[], bool]] = None,
    process_name: str = "Process"
) -> bool:
    """
    Run a subprocess with cancellation support.
    
    This function executes a subprocess and monitors it for completion or
    cancellation. If the cancel_checker function returns True, the process
    is terminated gracefully (or killed if necessary).
    
    Args:
        cmd: Command and arguments to execute as a list
        on_complete: Optional callback function to call with success status
        cancel_checker: Optional function that returns True if cancellation requested
        process_name: Name of the process for logging purposes
        
    Returns:
        True if process completed successfully, False otherwise
        
    Examples:
        >>> def check_cancel():
        ...     return user_clicked_cancel
        >>> success = run_cancellable_process(
        ...     ["long_running_command", "arg1", "arg2"],
        ...     on_complete=lambda s: print(f"Done: {s}"),
        ...     cancel_checker=check_cancel,
        ...     process_name="Long Task"
        ... )
    """
    # Check for cancellation before starting
    if cancel_checker and cancel_checker():
        print(f"{process_name} cancelled by user")
        if on_complete:
            on_complete(success=False)
        return False
    
    success = False
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Poll the process and check for cancellation
        while process.poll() is None:
            if cancel_checker and cancel_checker():
                print(f"Cancelling {process_name}")
                process.terminate()
                try:
                    process.wait(timeout=PROCESS_TERMINATION_TIMEOUT)
                except subprocess.TimeoutExpired:
                    print(f"Process did not terminate gracefully, killing {process_name}")
                    process.kill()
                    process.wait()
                print(f"{process_name} cancelled")
                if on_complete:
                    on_complete(success=False)
                return False
        
        # Check if process completed successfully
        if process.returncode == 0:
            success = True
        else:
            stderr = process.stderr.read().decode() if process.stderr else ""
            print(f"{process_name} failed with error: {stderr}")
            
    except subprocess.CalledProcessError as e:
        print(f"{process_name} failed with error: {e}")
    except FileNotFoundError as e:
        print(f"Command not found: {e}")
    
    # Send completion callback
    if on_complete:
        on_complete(success=success)
    
    return success
