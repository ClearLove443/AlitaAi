"""Tests for the CodingAgent class."""
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock

from alita.core.coding_agent import CodingAgent, Message
from autogen_core._single_threaded_agent_runtime import SingleThreadedAgentRuntime

class TestCodingAgent:
    """Test cases for CodingAgent."""

    @pytest.mark.asyncio
    async def test_handle_message(self, mock_chat_completion_client):
        """Test message handling in CodingAgent."""
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        # Setup runtime and register agent
        runtime = SingleThreadedAgentRuntime()
        runtime.start()
        try:
            # Create a proper mock response that matches what the code expects
            class MockResponse:
                def __init__(self, content):
                    self.content = content
                    self.tool_calls = None
            
            # Set up the mock client
            mock_response = MockResponse("Test response")
            mock_chat_completion_client.create = AsyncMock(return_value=mock_response)
            
            # Register the agent factory with the mock client
            logger.debug("Registering agent factory...")
            await CodingAgent.register(
                runtime=runtime,
                type="test_agent",
                factory=lambda: CodingAgent(model_client=mock_chat_completion_client)
            )
            
            # Get the agent instance
            logger.debug("Getting agent instance...")
            agent_id = await runtime.get("test_agent")
            agent = await runtime.try_get_underlying_agent_instance(agent_id, type=CodingAgent)
            
            # Create test message and context
            logger.debug("Creating test message and context...")
            mock_message = Message(content="Test message")
            mock_ctx = MagicMock()
            
            # Test
            logger.debug("Calling handle_message...")
            await agent.handle_message(mock_message, mock_ctx)
            
            # Assertions
            logger.debug("Verifying assertions...")
            mock_chat_completion_client.create.assert_called_once()
            assert len(agent._chat_history) == 3  # System + User + Assistant messages
            
        except Exception as e:
            logger.error(f"Test failed with error: {e}")
            raise
        finally:
            # Clean up
            logger.debug("Cleaning up...")
            await runtime.stop()
