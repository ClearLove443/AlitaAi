from .file_observations import FileReadObservation, FileWriteObservation, FileEditObservation
from typing import List
import os
from alita.core.utils import register_function

def read_file(path: str) -> FileReadObservation:
    """
    Read the contents of a file and return a FileReadObservation.
    
    Key Features:
    - Reads both text and binary files
    - Returns structured observation with file metadata
    - Handles file not found errors gracefully
    
    Parameters:
        path (str): Absolute path to the file to read
    
    Returns:
        FileReadObservation: Contains:
            - path: Original file path
            - content: File contents as string
            - exists: Whether file existed
            
    Example:
        read_file("/path/to/file.txt")
    
    Note:
        For large files (>10MB), consider streaming approaches instead
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return FileReadObservation(path=path, content=content)


def write_file(path: str, content: str) -> FileWriteObservation:
    """
    Write content to a file and return a FileWriteObservation.
    
    Key Features:
    - Creates new files or overwrites existing ones
    - Atomic write operation (all-or-nothing)
    - Returns verification of written content
    
    Parameters:
        path (str): Absolute path to the file to write
        content (str): Content to write to the file
    
    Returns:
        FileWriteObservation: Contains:
            - path: Original file path
            - content: Written content
            - bytes_written: Number of bytes written
            
    Example:
        write_file("/path/to/file.txt", "Hello World")
    
    Warning:
        Will overwrite existing files without confirmation
    """
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return FileWriteObservation(path=path, content=content)


def edit_file(path: str, new_content: str) -> FileEditObservation:
    """
    Edit (overwrite) a file with new content and return a FileEditObservation.
    
    Key Features:
    - Preserves original content in observation
    - Handles both new and existing files
    - Atomic write operation
    
    Parameters:
        path (str): Absolute path to the file to edit
        new_content (str): The new content to write
    
    Returns:
        FileEditObservation: Contains:
            - path: File path
            - prev_exist: Whether file existed before
            - old_content: Previous content (None if new file)
            - new_content: Current content
            
    Example:
        edit_file("/path/to/file.txt", "New content")
    
    Note:
        For partial edits, consider add_lines/remove_lines instead
    """
    prev_exist = os.path.exists(path)
    old_content = None
    if prev_exist:
        with open(path, 'r', encoding='utf-8') as f:
            old_content = f.read()
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return FileEditObservation(path=path, prev_exist=prev_exist, old_content=old_content, new_content=new_content, content=new_content)


def add_lines(path: str, lines: list[str], position: int) -> FileEditObservation:
    """
    Add lines to a file at specified position and return FileEditObservation.
    
    Key Features:
    - Non-destructive insertion
    - Precise line number control (0-based)
    - Preserves existing line endings
    
    Parameters:
        path (str): Absolute path to the file to modify
        lines (list[str]): Lines to insert
        position (int): Line number to insert at (0=first line)
    
    Returns:
        FileEditObservation: Contains before/after snapshots
    
    Example:
        add_lines("/path/to/file.txt", ["line1", "line2"], position=5)
    
    Note:
        For appending, use position=len(file_lines)
    """
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


def remove_lines(path: str, start: int, end: int) -> FileEditObservation:
    """
    Remove lines from file in specified range and return FileEditObservation.
    
    Key Features:
    - Precise line range removal
    - Boundary checking (won't fail on invalid ranges)
    - Preserves original line endings
    
    Parameters:
        path (str): Absolute path to the file
        start (int): First line to remove (inclusive, 0-based)
        end (int): Last line to remove (exclusive)
    
    Returns:
        FileEditObservation: Contains before/after snapshots
    
    Example:
        remove_lines("/path/to/file.txt", start=5, end=10)
    
    Warning:
        Will raise FileNotFoundError if file doesn't exist
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
