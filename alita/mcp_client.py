import json
from langchain_mcp_adapters.client import MultiServerMCPClient


class MCPClientWrapper:
    def __init__(self, config_path="mcp.json"):
        with open(config_path, "r") as f:
            config = json.load(f)
        self.client = MultiServerMCPClient(config)

    async def get_tools(self):
        return await self.client.get_tools()
