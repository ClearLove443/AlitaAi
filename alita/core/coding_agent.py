from langchain_core.messages.ai import AIMessage
from langchain_openai import ChatOpenAI

import tempfile
import asyncio
import json
import inspect
import logging
from typing import Any, Awaitable, Callable, List, Optional, Dict
from dataclasses import dataclass
from .execute_bash_command_tmux import execute_bash_command_tmux
from .utils import FUNCTION_REGISTRY

from .prompts.coding_agent_prompt import SYSTEM_PROMPT_TEMPLATE, SYSTEM_PREFIX, SYSTEM_SUFFIX, RUNNING_EXAMPLE

logger = logging.getLogger(__name__)

@dataclass
class Message:
    content: str

@dataclass
class Memory:
    content: str

class CodingAgent():
    def __init__(
        self, 
        model_client: ChatOpenAI,
        tools: List[Callable[..., Any] | Callable[..., Awaitable[Any]]] | None = None,
        memory: Optional[Memory] = None,
        ) -> None:
        
        self._model_client = model_client.bind_tools(tools)
        self._tools = tools  # Initialize tools list
        
    def _construct_full_prompt(self, task: str) -> str:
        # return SYSTEM_PROMPT_TEMPLATE.format(
        #     PREFIX=SYSTEM_PREFIX,
        #     EXAMPLE=RUNNING_EXAMPLE,
        #     TOOLS="",  # TODO We'll add tools later
        #     SUFFIX=SYSTEM_SUFFIX,
        #     TASK=task,
        #     MEMORY=""  # TODO We'll add memory later
        # )

        return """
        you are helpful coding assistant. Make sure to output TERMINATE when you think the task is fully completed.

        ------------ Task Started ---------------
        Task: {task}

        """.format(task=task)


    def _has_tool_calls(self, result: AIMessage) -> bool:
        return 'tool_calls' in result.additional_kwargs and result.additional_kwargs['tool_calls']


    def _call_llm(self) -> AIMessage:
        return self._model_client.invoke(self._full_system_prompt)


    def _execute_function_call(self,tool_call: Dict[str, Any]) -> str:
        """Execute a function call from the LLM response.
        
        Args:
            tool_call: Dictionary containing function call information
            
        Returns:
            str: Result of the function execution
        """
        try:
            # Extract function name and arguments
            func_name = tool_call['name']
            args = tool_call['args']
            
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
            return str(result)
            
        except Exception as e:
            return f"Error executing function call: {str(e)}"

    
    def _should_terminate(self, result: AIMessage) -> bool:
        return 'TERMINATE' in result.content
    
    
    async def run(self, message: str) -> None:
        logger.info(f"Received message: {message}")
        # print(FUNCTION_REGISTRY)
        
        self._full_system_prompt = self._construct_full_prompt(task=message)
        

        while True:
            logger.info(f"Full system prompt: {self._full_system_prompt}")
            result = self._call_llm()
            logger.info(f"LLM Result: {result}")
            
            if self._should_terminate(result):
                logger.info(f"Final Output: {result.content}")
                break
            
            self._full_system_prompt += result.content + "\n"
            

            if self._has_tool_calls(result):
                additional_kwargs = result.additional_kwargs

                self._full_system_prompt += json.dumps(additional_kwargs['tool_calls']) + "\n"
                
                for tool_call in additional_kwargs['tool_calls']:
                    if 'function' in tool_call:
                        # Convert the function call to the expected format
                        func_call = {
                            'name': tool_call['function']['name'],
                            'args': json.loads(tool_call['function']['arguments'])
                        }
                        result = self._execute_function_call(func_call)
                        print(f"\nFunction call result: {result}")
                        
                        self._full_system_prompt += result + "\n"

                

            
        