"""Pytest configuration and fixtures for Alita AI tests."""
import pytest
from unittest.mock import Mock, MagicMock

@pytest.fixture
def mock_chat_completion_client():
    """Mock ChatCompletionClient for testing using configuration from config.toml."""
    mock = Mock()
    mock.model_info = {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/",
        "function_calling": True,
        "vision": False,
        "json_output": False,
        "family": "deepseek"
    }
    return mock
