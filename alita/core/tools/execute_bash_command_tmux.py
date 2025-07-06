"""
A standalone utility to execute bash commands in a tmux session, capture the output, and return the result.
"""

import os
import time
import uuid
from typing import Optional, Dict, Any
import libtmux

from alita.core.utils import register_function

@register_function
def execute_bash_command_tmux(command: str, work_dir: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Description:Execute a bash command in a new tmux session and capture its output.
    
    This function creates a temporary tmux session, executes the specified command in a bash shell,
    captures both the command output and exit status, and returns them in a structured format.
    The session is automatically cleaned up after command execution or timeout.
    
    Args:
        command (str): The bash command to execute. Can be any valid shell command or script.
        work_dir (Optional[str]): The working directory for the command. If None, uses the current
                                 working directory of the calling process.
        timeout (int): Maximum time in seconds to wait for command completion before timing out.
                      Default is 30 seconds.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'output' (str): The combined stdout and stderr output of the command.
            - 'success' (bool): True if command executed successfully (exit code 0), False otherwise.
            - 'error' (Optional[str]): Error message if an exception occurred, None otherwise.
            - 'exit_code' (int): The exit code of the command. -1 if command timed out or failed to execute.
    
    Raises:
        ImportError: If the required 'libtmux' package is not installed.
        RuntimeError: If there's an issue with tmux server communication.
    
    Example:
        >>> result = execute_bash_command_tmux("ls -la", "/tmp")
        >>> if result['success']:
        ...     print(f"Command output: {result['output']}")
        ... else:
        ...     print(f"Command failed with code {result['exit_code']}: {result['error']}")
    
    Notes:
        - Each command runs in a fresh tmux session to ensure isolation.
        - The command is executed with bash's -c flag in a new session.
        - The function handles cleanup of temporary tmux sessions.
        - Output is captured from the tmux pane after command completion.
        - Exit code is captured by appending '; echo EXIT_CODE:$?' to the command.
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

    return {
        'output': output,
        'success': error is None and exit_code == 0,
        'error': error,
        'exit_code': exit_code,
    }