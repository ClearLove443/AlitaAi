import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import json

# from langchain_community.chat_models.openai import ChatOpenAI
from langchain_openai import ChatOpenAI

import os
from dotenv import load_dotenv

from mcp_client import MCPClientWrapper

load_dotenv()

# with open("mcp.json", "r") as f:
#     config = json.load(f)


async def main():

    # client = MultiServerMCPClient(config)

    # tools = await client.get_tools()
    mcp = MCPClientWrapper()
    tools = await mcp.get_tools()
    # for tool in tools:
    #     args = f"\nParameters:"
    #     if hasattr(tool, "args") and isinstance(tool.args, dict):
    #         for idx, (arg, spec) in enumerate(tool.args.items(), 1):
    #             arg_type = spec.get("type", "unknown")
    #             args += f"\n  ({idx}) {arg} ({arg_type}): {spec.get('description', '')}"

    #     args += "\n"
    #     print(args)
    base_url = os.getenv("BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(base_url=base_url, api_key=api_key, model="deepseek-chat")
    prompt = """
    Please use my mcps for the following things:

    sequential thinking mcp - for planning each step and ensuring we are completely this process to its maximum
    context7 - during reseach and also before yo implement any new third party API or change to the structure of the project or anything
    server-filesystem - for reading and writing files, you must use this mcp to read and write files, do not use any other method
    github - You have access to an environment variable, `GITHUB_PERSONAL_ACCESS_TOKEN`, which allows you to interact with
the GitHub API, for creating github repo, issues, pull requests, etc, you must create these under ClearLove443.
    you must first read the up to date documentation on that thing. This is extremely important, and you cannot not do this at any time
    you must always check documentation as things may have changed since you were trained.
      """
    # prompt = ""
    agent = create_react_agent(llm, tools, prompt=prompt)
    # math_response = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"})
    context7_response = await agent.ainvoke(
        {
            "messages": "write a spring boot application that uses a REST API to get the current weather in a city, then save to workspace folder, and push to github new public repo spring-boot-weather-app",
        },
        {"recursion_limit": 1000},
        stream_mode="values",
    )

    # res = await llm.ainvoke("what's (3 + 5) x 12?")
    # print(res)

    # print(math_response)
    print("==========")
    # print(context7_response)
    for msg in context7_response["messages"]:
        print(f"{type(msg).__name__}: {msg.content}")
        # 如果是AIMessage并且有tool_calls
        if hasattr(msg, "additional_kwargs"):
            tool_calls = msg.additional_kwargs.get("tool_calls")
            if tool_calls:
                for call in tool_calls:
                    name = call.get("function", {}).get("name") or call.get("name")
                    arguments = call.get("function", {}).get("arguments") or call.get(
                        "args"
                    )
                    print(f"  tool_call name: {name}")
                    print(f"  tool_call arguments: {arguments}")


if __name__ == "__main__":
    asyncio.run(main())
