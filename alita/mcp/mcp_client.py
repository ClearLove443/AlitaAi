import json
from langchain_mcp_adapters.client import MultiServerMCPClient


class MCPClientWrapper:
    def __init__(self, config_path="mcp.json"):
        with open(config_path, "r") as f:
            config = json.load(f)
        self.client = MultiServerMCPClient(config)

    async def get_tools(self):
        tools = await self.client.get_tools()
        # return [self.convert_tool(tool) for tool in tools]
        return tools

    # def convert_tool(self, tool):
    #     """
    #     Convert a tool to a format compatible with langchain.
    #     """
    #     return {"__name__": tool.name, "__doc__": tool.description}
