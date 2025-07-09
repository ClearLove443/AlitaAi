from enum import Enum

class ObservationType(str, Enum):
    READ = 'read'
    WRITE = 'write'
    EDIT = 'edit'
    # Add more as needed for your application

class FileEditSource(str, Enum):
    LLM_BASED_EDIT = 'llm_based_edit'
    CUSTOM = 'custom'

class FileReadSource(str, Enum):
    DEFAULT = 'default'
    CUSTOM = 'custom'
