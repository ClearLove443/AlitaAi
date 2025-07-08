from dataclasses import dataclass
from typing import List
from .file_tools import read_file, write_file, edit_file, add_lines, remove_lines
from .observation import Observation
from alita.core.utils import register_function

@dataclass
class FileAction:
    pass

@dataclass
class FileReadAction(FileAction):
    path: str

@dataclass
class FileWriteAction(FileAction):
    path: str
    content: str

@dataclass
class FileEditAction(FileAction):
    path: str
    new_content: str

@dataclass
class FileAddLinesAction(FileAction):
    path: str
    lines: List[str]
    position: int

@dataclass
class FileRemoveLinesAction(FileAction):
    path: str
    start: int
    end: int

@register_function
def execute_file_action(action):
    """
    Unified interface to execute file actions. Accepts either a FileAction subclass instance or a dict with a 'type' field (one of 'read', 'write', 'edit', 'add_lines', 'remove_lines').
    Dispatches to the appropriate file operation (read, write, edit, add lines, remove lines).
    """
    # Accept dict input for agent tool call compatibility
    if isinstance(action, dict):
        action_type = action.get('type')
        if action_type == 'read':
            return read_file(action['path'])
        elif action_type == 'write':
            return write_file(action['path'], action['content'])
        elif action_type == 'edit':
            return edit_file(action['path'], action['new_content'])
        elif action_type == 'add_lines':
            return add_lines(action['path'], action['lines'], action['position'])
        elif action_type == 'remove_lines':
            return remove_lines(action['path'], action['start'], action['end'])
        else:
            raise ValueError(f"Unknown file action type: {action_type}")