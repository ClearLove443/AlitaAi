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
from alita.core.tools.execute_bash_command_tmux import execute_bash_command_tmux
from alita.core.tools.files import read_file, write_file, edit_file, add_lines, remove_lines
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
    tools = [
        read_file,
        write_file,
        edit_file,
        add_lines,
        remove_lines,
        execute_bash_command_tmux
    ]
    coding_agent = CodingAgent(model_client=model_client, tools=tools)
    
    await coding_agent.run("Remove the greet() function from the autoTest/hello_world.py file, leaving only the Hello World print statement.")

if __name__ == "__main__":
    asyncio.run(main())