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


from alita.core.coding_agent import CodingAgent
from alita.core.execute_bash_command_tmux import execute_bash_command_tmux
from alita.config import llm_config
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

async def main():
    # Create the model client
    logger.info("Creating OpenAI chat completion client...")
    model_client = ChatOpenAI(
        model=llm_config.model,
        api_key=llm_config.api_key,
        base_url=llm_config.base_url
    )

    # Create an embedded runtime
    coding_agent = CodingAgent(model_client=model_client, tools=[execute_bash_command_tmux])
    
    await coding_agent.run("what are the files in current directory")

if __name__ == "__main__":
    asyncio.run(main())