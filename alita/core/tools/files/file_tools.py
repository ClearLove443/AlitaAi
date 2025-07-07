from .file_observations import FileReadObservation, FileWriteObservation, FileEditObservation
from typing import List
import os
from alita.core.utils import register_function

@register_function
def read_file(path: str) -> FileReadObservation:
    """
    Read the contents of a file and return a FileReadObservation.

    Args:
        path (str): The path to the file to read.

    Returns:
        FileReadObservation: Observation object containing the file path and content.

    Tool Metadata:
        name: "read_file"
        description: "Read the contents of a file and return an observation object."
        parameters:
            path: "The path to the file to read."
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return FileReadObservation(path=path, content=content)
@register_function
def write_file(path: str, content: str) -> FileWriteObservation:
    """
    Write content to a file and return a FileWriteObservation.

    Args:
        path (str): The path to the file to write.
        content (str): The content to write to the file.

    Returns:
        FileWriteObservation: Observation object containing the file path and written content.

    Tool Metadata:
        name: "write_file"
        description: "Write content to a file and return an observation object."
        parameters:
            path: "The path to the file to write."
            content: "The content to write to the file."
    """
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return FileWriteObservation(path=path, content=content)
@register_function
def edit_file(path: str, new_content: str) -> FileEditObservation:
    """
    Edit (overwrite) a file with new content and return a FileEditObservation.

    Args:
        path (str): The path to the file to edit.
        new_content (str): The new content to write to the file.

    Returns:
        FileEditObservation: Observation object containing the file path, previous content, and new content.

    Tool Metadata:
        name: "edit_file"
        description: "Edit (overwrite) a file with new content and return an observation object."
        parameters:
            path: "The path to the file to edit."
            new_content: "The new content to write to the file."
    """
    prev_exist = os.path.exists(path)
    old_content = None
    if prev_exist:
        with open(path, 'r', encoding='utf-8') as f:
            old_content = f.read()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return FileEditObservation(path=path, prev_exist=prev_exist, old_content=old_content, new_content=new_content, content=new_content)
@register_function
def add_lines(path: str, lines: list[str], position: int) -> FileEditObservation:
    """
    Add lines to a file at the specified position and return a FileEditObservation.

    Args:
        path (str): The path to the file to modify.
        lines (list[str]): The lines to add.
        position (int): The line index at which to insert the new lines (0-based).

    Returns:
        FileEditObservation: Observation object with before/after content and edit details.

    Tool Metadata:
        name: "add_lines"
        description: "Add lines to a file at the specified position and return an observation object."
        parameters:
            path: "The path to the file to modify."
            lines: "The lines to add."
            position: "The line index at which to insert the new lines (0-based)."
    """
    # Ensure lines is a list (not typing.List)
    lines = list(lines)
    prev_exist = os.path.exists(path)
    old_content = None
    if prev_exist:
        with open(path, 'r', encoding='utf-8') as f:
            old_content = f.read()
        file_lines = old_content.splitlines()
    else:
        file_lines = []
    for i, line in enumerate(lines):
        file_lines.insert(position + i, line)
    new_content = '\n'.join(file_lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return FileEditObservation(path=path, prev_exist=prev_exist, old_content=old_content, new_content=new_content, content=new_content)
@register_function
def remove_lines(path: str, start: int, end: int) -> FileEditObservation:
    """
    Remove lines from a file in the specified range and return a FileEditObservation.

    Args:
        path (str): The path to the file to modify.
        start (int): The starting line index (inclusive, 0-based).
        end (int): The ending line index (exclusive, 0-based).

    Returns:
        FileEditObservation: Observation object with before/after content and edit details.

    Tool Metadata:
        name: "remove_lines"
        description: "Remove lines from a file in the specified range and return an observation object."
        parameters:
            path: "The path to the file to modify."
            start: "The starting line index (inclusive, 0-based)."
            end: "The ending line index (exclusive, 0-based)."
    """
    prev_exist = os.path.exists(path)
    if not prev_exist:
        raise FileNotFoundError(f"File {path} does not exist.")
    with open(path, 'r', encoding='utf-8') as f:
        old_content = f.read()
    file_lines = old_content.splitlines()
    del file_lines[start:end]
    new_content = '\n'.join(file_lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return FileEditObservation(path=path, prev_exist=prev_exist, old_content=old_content, new_content=new_content, content=new_content)
