from dataclasses import dataclass
from typing import List
from .file_tools import read_file, write_file, edit_file, add_lines, remove_lines
from .observation import Observation
from alita.core.utils import register_function

@dataclass
class FileAction:
    path: str

class FileReadAction(FileAction):
    type = "read"

@dataclass
class FileWriteAction(FileAction):
    content: str
    type = "write"

@dataclass
class FileEditAction(FileAction):
    new_content: str
    type = "edit"

@dataclass
class FileAddLinesAction(FileAction):
    lines: List[str]
    position: int
    type = "add_lines"

@dataclass
class FileRemoveLinesAction(FileAction):
    start: int
    end: int
    type = "remove_lines"


def _file_action_factory(action):
    if isinstance(action, FileAction):
        return action
    if not isinstance(action, dict):
        raise TypeError("Action must be a FileAction or dict")
    action_type = action.get('type')
    if action_type == 'read':
        return FileReadAction(path=action['path'])
    elif action_type == 'write':
        return FileWriteAction(path=action['path'], content=action['content'])
    elif action_type == 'edit':
        return FileEditAction(path=action['path'], new_content=action['new_content'])
    elif action_type == 'add_lines':
        return FileAddLinesAction(path=action['path'], lines=action['lines'], position=action['position'])
    elif action_type == 'remove_lines':
        return FileRemoveLinesAction(path=action['path'], start=action['start'], end=action['end'])
    else:
        raise ValueError(f"Unknown file action type: {action_type}")

_ACTION_DISPATCH = {
    'read':   lambda a: read_file(a.path),
    'write':  lambda a: write_file(a.path, a.content),
    'edit':   lambda a: edit_file(a.path, a.new_content),
    'add_lines': lambda a: add_lines(a.path, a.lines, a.position),
    'remove_lines': lambda a: remove_lines(a.path, a.start, a.end),
}

@register_function
def execute_file_action(action):
    """
    Unified interface to execute file actions.

    Parameters:
        action (dict or FileAction subclass): The file action to perform. If a dict, it must have a 'type' key and the required fields for that action type.

    Supported action types and required parameters:
        - "read" or "FileReadAction":
            { "type": "read", "path": "<file_path>" }
        - "write" or "FileWriteAction":
            { "type": "write", "path": "<file_path>", "content": "<text>" }
        - "edit" or "FileEditAction":
            { "type": "edit", "path": "<file_path>", "new_content": "<text>" }
        - "add_lines" or "FileAddLinesAction":
            { "type": "add_lines", "path": "<file_path>", "lines": [<str>, ...], "position": <int> }
        - "remove_lines" or "FileRemoveLinesAction":
            { "type": "remove_lines", "path": "<file_path>", "start": <int>, "end": <int> }

    Returns:
        Observation: The result of the file action.

    Notes:
        - For compatibility with agent tool calls, dicts are converted to the appropriate FileAction subclass.
        - The function dispatches to the appropriate file operation (read, write, edit, add lines, remove lines) based on the action type.
    """
    action_obj = _file_action_factory(action)
    handler = _ACTION_DISPATCH.get(action_obj.type)
    if handler:
        return handler(action_obj)
    raise ValueError(f"Unknown FileAction type: {action_obj.type}")