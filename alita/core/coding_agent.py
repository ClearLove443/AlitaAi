import json
import inspect
import logging
import re
from typing import Any, Awaitable, Callable, List, Optional, Dict
from dataclasses import dataclass

from langchain_core.messages.ai import AIMessage
from langchain_core.messages.tool import ToolCall
from langchain_openai import ChatOpenAI

from alita.core.tools.files.observation import Observation
from alita.core.tools.finish_observations import FinishObservation
from alita.core.utils import FUNCTION_REGISTRY
from alita.core.prompts.coding_agent_prompt import (
    SYSTEM_PROMPT_TEMPLATE,
    SYSTEM_PREFIX,
    RUNNING_EXAMPLE,
    SYSTEM_SUFFIX,
    EXTRA_INFO
)


logger = logging.getLogger(__name__)

# Enable full LLM prompt logging
# langchain.debug = True


@dataclass
class Message:
    content: str


@dataclass
class Memory:
    content: str


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]
    id: Optional[str] = None
    type: Optional[str] = None


class CodingAgent:
    def __init__(
        self,
        model_client: ChatOpenAI,
        work_dir: str = "./workspace",
        tools: List[Callable[..., Any] | Callable[..., Awaitable[Any]]] | None = None,
        memory: Optional[Memory] = None,
    ) -> None:

        self._model_client = model_client.bind_tools(tools)
        self._work_dir = work_dir
        if tools:
            self._tools_prompt = self._construct_tools_prompt(tools)

        self._iter_count = 0

    def _construct_tools_prompt(
        self, tools: List[Callable[..., Any] | Callable[..., Awaitable[Any]]]
    ) -> str:
        tool_prompt = "You have access to following functions/tools:\n\n"
        index = 0
        for tool in tools:
            index += 1
            tool_name = getattr(tool, "__name__", getattr(tool, "name", str(tool)))
            tool_prompt += f"---- BEGIN FUNCTION #{index} {tool_name} ----\n"
            tool_prompt += getattr(tool, "description", None) or getattr(
                tool, "__doc__", None
            )

            if hasattr(tool, "args") and isinstance(tool.args, dict):

                args = f"\nParameters:"
                for idx, (arg, spec) in enumerate(tool.args.items(), 1):
                    arg_type = spec.get("type", "unknown")
                    args += f"\n  ({idx}) {arg} ({arg_type}): {spec.get('description', '')}"

                args += "\n"
                tool_prompt += args
            
            tool_prompt += f"\n---- END FUNCTION #{index} ----\n\n"

        return tool_prompt

    def _construct_full_prompt(self, task: str) -> str:
        return SYSTEM_PROMPT_TEMPLATE.format(
            prefix=SYSTEM_PREFIX,
            tools=self._tools_prompt,
            example=RUNNING_EXAMPLE,
            task=task,
            extra_info=EXTRA_INFO,
            suffix=SYSTEM_SUFFIX.format(work_dir=self._work_dir),
        )

    def _call_llm(self) -> AIMessage:
        return self._model_client.invoke(self._full_system_prompt)

    def _execute_function_call(self, tool_call: ToolCall) -> Observation:
        """Execute a function call from the LLM response.

        Args:
            tool_call: Dictionary containing function call information

        Returns:
            str: Result of the function execution
        """
        try:
            # Extract function name and arguments
            func_name = tool_call.name
            args = tool_call.args

            # Get the function from registry
            func = FUNCTION_REGISTRY.get(func_name)

            if not func:
                return f"Error: Function '{func_name}' not found in registry"

            # Get the function's parameter types
            sig = inspect.signature(func)
            params = sig.parameters

            # Convert arguments to the correct types
            typed_args = {}
            for param_name, param in params.items():
                if param_name in args:
                    param_type = param.annotation
                    if param_type != inspect.Parameter.empty:
                        # Convert to the correct type
                        typed_args[param_name] = param_type(args[param_name])
                    else:
                        typed_args[param_name] = args[param_name]

            # Call the function with the typed arguments
            result = func(**typed_args)
            return result

        except Exception as e:
            return Observation(content=f"Error executing function call: {str(e)}")

    def _parse_tool_call_in_llm_content(
        self, llm_output: AIMessage
    ) -> List[ToolCall] | None:
        """
        Extracts tool call message from the end of LLM output content and converts to ToolCall objects.
        Returns None if no tool call is found.
        """
        if not llm_output.content:
            return None

        # TODO need to test this thoroughly
        pattern = r"(?s)(<.*?>|\{.*?\})$"
        match = re.search(pattern, llm_output.content.strip())

        if not match:
            return None

        try:
            # Handle both JSON and XML formats
            if match.group(0).startswith("{"):
                tool_call_dict = json.loads(match.group(0))
                return [ToolCall(**tool_call_dict)] if tool_call_dict else None
            else:
                # For XML, we'd need additional parsing logic
                # Placeholder for XML parsing implementation
                return None
        except json.JSONDecodeError:
            logger.error("Failed to parse tool call from LLM output content")
            return None

    def _get_tool_calls(self, llm_output: AIMessage) -> List[ToolCall] | None:
        """
        Two scenarios to handle:
        1. tool_calls in llm_output is not empty
        2. tool_calls text in llm_output.content, not in 'tool_calls' field

        Prioritize scenario 1, if scenario 1 is not met, then scenario 2
        """
        tool_calls = []
        if hasattr(llm_output, "tool_calls") and llm_output.tool_calls:
            for tool_call in llm_output.tool_calls:
                tool_calls.append(ToolCall(**tool_call))
            return tool_calls

        else:
            return self._parse_tool_call_in_llm_content(llm_output)

    def _handle_tool_calls(self, llm_output: AIMessage) -> Observation | None:
        tool_calls = self._get_tool_calls(llm_output)
        if tool_calls:
            # confirm should only have one tool call per time
            if len(tool_calls) > 1:
                logger.warning(
                    "Multiple tool calls detected. Only the first tool call will be executed."
                )
            tool_call = tool_calls[0]
            observation = self._execute_function_call(tool_call)
            # logger.info(f"\nFunction call result: {observation}")

            # self._full_system_prompt += f"{observation}\n\n" + "-"*20 + "\n\n"
            return observation

        return None

    async def run(self, message: str) -> None:
        logger.info(f"Received message: {message}")

        self._full_system_prompt = (
            self._construct_full_prompt(task=message) + "-" * 20 + "\n\n"
        )

        logger.info(f"Full system prompt: {self._full_system_prompt}")
        while True:
            self._iter_count += 1
            print(f"----- Iteration {self._iter_count} -----")
            logger.info(f"----- Iteration {self._iter_count} -----")
            # logger.info(f"Full system prompt: {self._full_system_prompt}")

            ### - call LLM
            llm_output: AIMessage = self._call_llm()
            logger.info(f"LLM Result: {llm_output}")

            ### - call tool
            observation: Observation | None = self._handle_tool_calls(llm_output)

            logger.info(f"Tool call result: {observation}")

            ### - check whether terminate
            if isinstance(observation, FinishObservation):
                logger.info(f"Final Output:\n {observation}")
                break

            ### - construct prompt
            incremental_prompt = ""
            if observation:
                incremental_prompt = f"""
                {llm_output.content}\n{llm_output.tool_calls}\n\n{'-'*20}\n\n{observation}\n\n{'-'*20}\n\n
                """
            else:
                incremental_prompt = f"{llm_output.content}\n\n{'-'*20}\n\n"

            self._full_system_prompt += incremental_prompt
