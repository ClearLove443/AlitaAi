"""
A standalone utility to execute bash commands in a tmux session, capture the output, and return the result.
"""

import libtmux
import time
import uuid
import os
from typing import Optional, Dict, Any
from .utils import register_function


@register_function
def execute_bash_command_tmux(command: str, work_dir: Optional[str] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute a bash command in a new tmux session and capture its output.

    This function is designed to be compatible with LLM functional calls, accepting a bash command as input,
    running it safely in a tmux pane, and returning the output and status in a structured dictionary.

    Args:
        command (str): The bash command to execute.
        work_dir (str, optional): The working directory to run the command in. If None, uses the current directory.
        timeout (int, optional): Maximum number of seconds to wait for command completion. Default is 30 seconds.

    Returns:
        dict: A dictionary with the following keys:
            - 'output': The captured stdout/stderr output as a string.
            - 'success': True if the command ran successfully, False otherwise.
            - 'error': Error message if any exception occurred, else None.
            - 'exit_code': The exit code of the command, or None if not available.

    Example:
        result = execute_bash_command_tmux('ls -l /')
        if result['success']:
            print(result['output'])
        else:
            print('Error:', result['error'])
    """
    session_name = f"juno-tmp-{uuid.uuid4().hex[:8]}"
    server = libtmux.Server()
    session = None
    output = ''
    exit_code = None
    error = None
    try:
        session = server.new_session(session_name=session_name, attach=False, kill_session=True, start_directory=work_dir or os.getcwd())
        pane = session.attached_pane
        # Send the command and capture output
        pane.send_keys(command)
        # Wait for the command to finish
        start_time = time.time()
        while time.time() - start_time < timeout:
            pane_output = '\n'.join(pane.cmd('capture-pane', '-p').stdout)
            if pane_output.strip():
                output = pane_output
            # Try to detect end of command by checking for a new prompt (simple heuristic)
            if output.strip().endswith(('$', '#')):
                break
            time.sleep(0.5)
        # Try to get exit code
        pane.send_keys('echo $?')
        time.sleep(0.5)
        pane_output = '\n'.join(pane.cmd('capture-pane', '-p').stdout)
        lines = pane_output.strip().split('\n')
        for line in reversed(lines):
            if line.isdigit():
                exit_code = int(line)
                break
    except Exception as e:
        error = str(e)
    finally:
        if session is not None:
            session.kill_session()
    return {
        'output': output,
        'success': (error is None and (exit_code == 0 or exit_code is None)),
        'error': error,
        'exit_code': exit_code,
    }
