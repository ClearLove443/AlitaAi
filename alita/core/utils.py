from typing import Dict, Callable, Any


FUNCTION_REGISTRY: Dict[str, Callable] = {}

def register_function(func: Callable) -> Callable:
    """Decorator to register a function in the registry."""
    FUNCTION_REGISTRY[func.__name__] = func
    return func


