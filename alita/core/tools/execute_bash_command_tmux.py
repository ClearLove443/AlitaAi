"""
Standalone utility to execute bash commands in a tmux session, capture the output, and return the result.
"""
import os
import time
import uuid
from typing import Optional, Dict, Any
import libtmux
import json

from alita.core.utils import register_function
from alita.core.tools.bash_observations import BashObservation

@register_function
def execute_bash_command_tmux(command: str, work_dir: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute a bash command in an isolated tmux session with full output capture.
    
    Key Features:
    * Each command runs in a fresh tmux session to prevent environment contamination
    * Full output capture including stdout, stderr and exit code
    * Session cleanup after command completion
    * Timeout handling for long-running commands
    
    CRITICAL REQUIREMENTS:
    1. COMMAND SAFETY: Never execute destructive commands (rm -rf, mv, etc)
    2. ABSOLUTE PATHS: Always use absolute paths for file operations
    3. ISOLATION: Each command runs in a clean environment - set up required env vars explicitly
    4. OUTPUT HANDLING: Large outputs will be truncated to prevent memory issues
    
    Parameters:
      command (str): The bash command to execute
      timeout (int, optional): Maximum runtime in seconds (default: 30)
      work_dir (str, optional): Working directory for command (default: current working directory)
    
    Returns:
      BashObservation containing:
        - content (str): Command output (stdout + stderr)
        - command (str): The bash command executed
        - exit_code (int): Command's exit code
        - error (str): Error message if any
    
    Usage Examples:
    1. Basic command:
       execute_bash_command_tmux("ls -la /path/to/dir")
    
    2. With timeout:
       execute_bash_command_tmux("long_running_script.sh", timeout=120)
    
    3. With working directory:
       execute_bash_command_tmux("./script.sh", work_dir="/project/src")
    
    Security Notes:
    - Commands are NOT sanitized - implement input validation at call site
    - Never pass untrusted user input directly to this function
    - Consider using command allowlists in production
    """
    session_name = f"juno-tmp-{uuid.uuid4().hex[:8]}"
    server = libtmux.Server()
    session = None
    output = ""
    exit_code = 1  # Default to error state
    error = None

    try:
        # Create session with a known shell command
        session = server.new_session(
            session_name=session_name,
            attach=False,
            kill_session=True,
            start_directory=work_dir or os.getcwd(),
            window_command=f"bash -c '{command}; echo EXIT_CODE:$?; read -p \"Press enter to continue\"'"
        )
        pane = session.attached_pane
        
        # Wait for command to complete
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Get the current pane content
            pane_output = '\n'.join(pane.cmd('capture-pane', '-p').stdout)
            
            # Check if command has completed
            if 'EXIT_CODE:' in pane_output:
                # Split output and get exit code
                output, exit_info = pane_output.rsplit('EXIT_CODE:', 1)
                output = output.strip()
                
                # Extract exit code (should be the last non-empty line after EXIT_CODE:)
                exit_line = exit_info.strip().split('\n')[0].strip()
                try:
                    exit_code = int(exit_line)
                except (ValueError, IndexError):
                    exit_code = 1
                    error = f"Failed to parse exit code from: {exit_line}"
                break
                
            time.sleep(0.1)  # Small delay to prevent busy waiting
            
        else:
            error = "Command timed out"
            exit_code = -1

    except Exception as e:
        error = str(e)
        exit_code = -1
        
    finally:
        # Clean up the session
        if session:
            try:
                session.kill_session()
            except:
                pass

    return BashObservation(
        content=output,
        command=command,
        exit_code=exit_code,
        error=error,
    )