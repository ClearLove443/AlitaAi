import tempfile
import asyncio
import logging
from typing import Any, Awaitable, Callable, List, Optional
from dataclasses import dataclass

from autogen_core.tools import Tool, FunctionTool
from autogen_core.memory import Memory

from autogen_core import (
    DefaultTopicId,
    MessageContext,
    RoutedAgent,
    default_subscription,
    message_handler,
)
from autogen_core.code_executor import CodeBlock, CodeExecutor
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
    ModelFamily
)

from .prompts.coding_agent_prompt import SYSTEM_PROMPT_TEMPLATE, SYSTEM_PREFIX, SYSTEM_SUFFIX, RUNNING_EXAMPLE

logger = logging.getLogger(__name__)

@dataclass
class Message:
    content: str

@default_subscription
class CodingAgent(RoutedAgent):
    def __init__(
        self, 
        model_client: ChatCompletionClient,
        tools: List[Tool | Callable[..., Any] | Callable[..., Awaitable[Any]]] | None = None,
        memory: Optional[Memory] = None,
        ) -> None:
        
        super().__init__("A coding agent.")
        self._model_client = model_client
        self._tools = []  # Initialize tools list
        
        # TODO check this code from AssistantAgent
        if tools is not None:
            if model_client.model_info["function_calling"] is False:
                raise ValueError("The model does not support function calling.")
            for tool in tools:
                if isinstance(tool, Tool):
                    self._tools.append(tool)
                elif callable(tool):
                    if hasattr(tool, "__doc__") and tool.__doc__ is not None:
                        description = tool.__doc__
                    else:
                        description = ""
                    self._tools.append(FunctionTool(tool, description=description))
                else:
                    raise ValueError(f"Unsupported tool type: {type(tool)}")
        # Check if tool names are unique.
        tool_names = [tool.name for tool in self._tools]
        if len(tool_names) != len(set(tool_names)):
            raise ValueError(f"Tool names must be unique: {tool_names}")

        self._system_message = self._construct_system_prompt()
        self._chat_history: List[LLMMessage] = [
            SystemMessage(
                content=self._system_message,
            )
        ]

    def _construct_system_prompt(self) -> str:
        return SYSTEM_PROMPT_TEMPLATE.format(
            PREFIX=SYSTEM_PREFIX,
            EXAMPLE=RUNNING_EXAMPLE,
            TOOLS="",  # We'll add tools later
            SUFFIX=SYSTEM_SUFFIX,
        )

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        logger.info(f"Received message: {message.content}")

        self._chat_history.append(UserMessage(content=message.content, source="user"))


        # TODO handle tool calls

        # TODO handle memory

        logger.info("Sending message to model...")
        result = await self._model_client.create(self._chat_history, tools=self._tools)

        logger.info(f"Got response from model: {result.content}")
        
        self._chat_history.append(AssistantMessage(content=result.content, source="assistant"))

        


        logger.info("Sending response back...")

        # send message to self for multi-step responses
        # TODO need to add termination condition, otherwise it's running infinite loop
        await self.send_message(Message(result.content), recipient=self.id)
