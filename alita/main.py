import asyncio
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # This will override any existing logging configuration
)

# Enable debug logging for autogen-core
logging.getLogger('autogen_core').setLevel(logging.INFO)
logging.getLogger('autogen_ext').setLevel(logging.INFO)

from autogen_core import DefaultTopicId,SingleThreadedAgentRuntime
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient

from alita.core.coding_agent import CodingAgent
from alita.config import llm_config
from alita.core.coding_agent import Message

logger = logging.getLogger(__name__)

async def main():
    # Create the model client
    logger.info("Creating OpenAI chat completion client...")
    model_client = OpenAIChatCompletionClient(
        model=llm_config.model,
        api_key=llm_config.api_key,
        base_url=llm_config.base_url,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": False,
            "family": ModelFamily.GPT_4,
            "structured_output": True,
        },
    )

    # Create an embedded runtime
    logger.info("Creating agent runtime...")
    runtime = SingleThreadedAgentRuntime()

    # Register the coding agent factory
    logger.info("Registering coding agent factory...")
    await CodingAgent.register(
        runtime=runtime,
        type="coding",
        factory=lambda: CodingAgent(model_client=model_client)
    )
    
    # Get the agent instance from the runtime
    coding_agent = await runtime.get("coding")
    logger.info("Coding agent created with id: %s", coding_agent)


    # Start the runtime and send a message
    logger.info("Starting runtime...")
    runtime.start()
    
    logger.info("Sending initial message...")
    await runtime.publish_message(
        Message("how are you"), 
        DefaultTopicId()
    )

    # Wait for the runtime to stop
    logger.info("Waiting for runtime to stop...")
    await runtime.stop_when_idle()
    logger.info("Runtime stopped.")

if __name__ == "__main__":
    asyncio.run(main())