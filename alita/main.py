import asyncio
import logging

from alita.mcp.mcp_client import MCPClientWrapper

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,  # This will override any existing logging configuration
)

# Enable debug logging for autogen-core
logging.getLogger("autogen_core").setLevel(logging.INFO)
logging.getLogger("autogen_ext").setLevel(logging.INFO)


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
        temperature=0,
        api_key=llm_config.api_key,
        base_url=llm_config.base_url
    )

    mcp = MCPClientWrapper()
    mcp_tools = await mcp.get_tools()

    # print(mcp_tools)
    # return 

    # Create an embedded runtime
    tools = [
        execute_bash_command_tmux,
        finish,
        execute_file_action,
        # *mcp_tools,
    ]
    coding_agent = CodingAgent(model_client=model_client,work_dir="/Users/dongqiuyepu/Desktop/code/python/AlitaAi/workspace", tools=tools)

    code_write_prompt = """
    The working directory is empty right now. Write a restful service using python fastapi framework that returns hello world. Make sure it runs successfully.
    """

    code_investigate_prompt = """

    Investigate current directory and explain the execution flow of the code base. Don't terminate until you can explain the whole execution flow.

    """

    await coding_agent.run(code_write_prompt)

    # print(execute_bash_command_tmux.__doc__)


if __name__ == "__main__":
    asyncio.run(main())
