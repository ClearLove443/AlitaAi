import asyncio
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # This will override any existing logging configuration
)

# Enable debug logging for autogen-core
logging.getLogger('autogen_core').setLevel(logging.INFO)
logging.getLogger('autogen_ext').setLevel(logging.INFO)


from alita.core.coding_agent import CodingAgent
from alita.core.tools.execute_bash_command_tmux import execute_bash_command_tmux
from alita.core.tools.finish import finish
from alita.core.tools.files.file_action_executor import execute_file_action
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
        execute_bash_command_tmux,
        finish,
        execute_file_action,
    ]
    coding_agent = CodingAgent(model_client=model_client, tools=tools)
    
    code_write_prompt = """
    Create a new file in current directory named with test_output.py and write function to calculate fibonacci sequence using Python.
    """

    code_investigate_prompt = """
    
    Investigate current directory and explain the execution flow of the code base. Don't terminate until you can explain the whole execution flow.

    """


    await coding_agent.run(code_write_prompt)

    # print(execute_bash_command_tmux.__doc__)

if __name__ == "__main__":
    asyncio.run(main())