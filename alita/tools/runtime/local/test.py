import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily
from execute_bash_command_tmux import execute_bash_command_tmux

model_client = OpenAIChatCompletionClient(

    model="deepseek-chat",
    api_key="sk-016f4b2ac20246b9bf48eb1b0b187e82",
    base_url="https://api.deepseek.com/v1",
    timeout=60,
    model_info={
        "vision": False,
        "family": ModelFamily.R1,
        "function_calling": True,
        "json_output": True,
        "multiple_system_messages": False,
        "structured_output": False,
    }

)

agent = AssistantAgent(
    name="AssistantAgent",
    model_client=model_client,
    tools=[execute_bash_command_tmux],
    system_message="You are a helpful assistant.",
    reflect_on_tool_use=True,
    model_client_stream=True,  # Enable streaming tokens from the model client.
)


# Run the agent and stream the messages to the console.
async def main() -> None:
    await Console(agent.run_stream(task="I want to list all the files in current directory"))
    # Close the connection to the model client.
    await model_client.close()


# NOTE: if running this inside a Python script you'll need to use asyncio.run(main()).
# await main()
asyncio.run(main())