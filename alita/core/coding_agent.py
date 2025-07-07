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
from alita.core.prompts.coding_agent_prompt import RUNNING_EXAMPLE


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

class CodingAgent():
    def __init__(
        self, 
        model_client: ChatOpenAI,
        tools: List[Callable[..., Any] | Callable[..., Awaitable[Any]]] | None = None,
        memory: Optional[Memory] = None,
        ) -> None:
        
        self._model_client = model_client.bind_tools(tools)
        
        if tools:
            self._tools_prompt = self._construct_tools_prompt(tools)

        self._example_prompt = self._construct_example_prompt()
        self._iter_count = 0
        
    def _construct_example_prompt(self):
        return RUNNING_EXAMPLE

    def _construct_tools_prompt(self, tools: List[Callable[..., Any] | Callable[..., Awaitable[Any]]]) -> str:
        tool_prompt = "You have access to following functions/tools:\n\n"
        index = 0
        for tool in tools:
            index += 1
            tool_prompt += f"---- BEGIN FUNCTION #{index} {tool.__name__} ----\n"
            tool_prompt += tool.__doc__
            tool_prompt += f"\n---- END FUNCTION #{index} ----\n\n"

        return tool_prompt

    def _construct_full_prompt(self, task: str) -> str:
        return """
You are Alita, a helpful AI assistant that can interact with a computer to solve tasks.

<ROLE>
Your primary role is to assist users by executing commands, modifying code, and solving technical problems effectively. You should be thorough, methodical, and prioritize quality over speed.
* If the user asks a question, like "why is X happening", don't try to fix the problem. Just give an answer to the question.
</ROLE>

<EFFICIENCY>
* Each action you take is somewhat expensive. Wherever possible, combine multiple actions into a single action, e.g. combine multiple bash commands into one, using sed and grep to edit/view multiple files at once.
* When exploring the codebase, use efficient tools like find, grep, and git commands with appropriate filters to minimize unnecessary operations.
</EFFICIENCY>

<FILE_SYSTEM_GUIDELINES>
* When a user provides a file path, do NOT assume it's relative to the current working directory. First explore the file system to locate the file before working on it.
* If asked to edit a file, edit the file directly, rather than creating a new file with a different filename.
* For global search-and-replace operations, consider using `sed` instead of opening file editors multiple times.
</FILE_SYSTEM_GUIDELINES>

<PROBLEM_SOLVING_WORKFLOW>
1. EXPLORATION: Thoroughly explore relevant files and understand the context before proposing solutions
2. ANALYSIS: Consider multiple approaches and select the most promising one
3. TESTING:
   * For bug fixes: Create tests to verify issues before implementing fixes
   * For new features: Consider test-driven development when appropriate
   * If the repository lacks testing infrastructure and implementing tests would require extensive setup, consult with the user before investing time in building testing infrastructure
   * If the environment is not set up to run tests, consult with the user first before investing time to install all dependencies
4. IMPLEMENTATION: Make focused, minimal changes to address the problem
5. VERIFICATION: If the environment is set up to run tests, test your implementation thoroughly, including edge cases. If the environment is not set up to run tests, consult with the user first before investing time to run tests.
</PROBLEM_SOLVING_WORKFLOW>

<TROUBLESHOOTING>
* If you've made repeated attempts to solve a problem but tests still fail or the user reports it's still broken:
  1. Step back and reflect on 5-7 different possible sources of the problem
  2. Assess the likelihood of each possible cause
  3. Methodically address the most likely causes, starting with the highest probability
  4. Document your reasoning process
* When you run into any major issue while executing a plan from the user, please don't try to directly work around it. Instead, propose a new plan and confirm with the user before proceeding.
</TROUBLESHOOTING>

<TOOL_USAGE>
- Tool calls should be json format, the schema is:
{{
  "name": NAME OF THE TOOL,
  "args": {{
    ARGUMENT_NAME: ARGUMENT_VALUE,
    ...
  }}
}}
- Always put your tool call in the end of your response, no suffix needed.
- Always explain your reasoning before using any tools
- Use tools to gather concrete information about the codebase
- One tool call at a time
</TOOL_USAGE>

{tools}

{example}

----------------Task Starts----------------
Task: {task}

""".format(tools=self._tools_prompt, example=self._example_prompt, task=task)


    def _call_llm(self) -> AIMessage:
        return self._model_client.invoke(self._full_system_prompt)


    def _execute_function_call(self,tool_call: ToolCall) -> Observation:
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
    

    def _parse_tool_call_in_llm_content(self, llm_output: AIMessage) -> List[ToolCall] | None:
        """
        Extracts tool call message from the end of LLM output content and converts to ToolCall objects.
        Returns None if no tool call is found.
        """
        if not llm_output.content:
            return None
        
        # TODO need to test this thoroughly
        pattern = r'(?s)(<.*?>|\{.*?\})$'
        match = re.search(pattern, llm_output.content.strip())
        
        if not match:
            return None
            
        try:
            # Handle both JSON and XML formats
            if match.group(0).startswith('{'):
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
        '''
        Two scenarios to handle:
        1. tool_calls in llm_output is not empty
        2. tool_calls text in llm_output.content, not in 'tool_calls' field

        Prioritize scenario 1, if scenario 1 is not met, then scenario 2
        '''
        tool_calls = []
        if hasattr(llm_output, 'tool_calls') and llm_output.tool_calls:
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
                logger.warning("Multiple tool calls detected. Only the first tool call will be executed.")
            tool_call = tool_calls[0]
            observation = self._execute_function_call(tool_call)
            logger.info(f"\nFunction call result: {observation}")

            # self._full_system_prompt += f"{observation}\n\n" + "-"*20 + "\n\n"
            return observation
        
        return None

    
    async def run(self, message: str) -> None:
        logger.info(f"Received message: {message}")
        
        self._full_system_prompt = self._construct_full_prompt(task=message) + "-"*20 + "\n\n"
        
        while True:
            self._iter_count += 1
            print(f'----- Iteration {self._iter_count} -----')
            logger.info(f'----- Iteration {self._iter_count} -----')
            logger.info(f"Full system prompt: {self._full_system_prompt}")

            ### - call LLM
            llm_output: AIMessage = self._call_llm()
            logger.info(f"LLM Result: {llm_output}")
            
            ### - call tool
            observation: Observation | None = self._handle_tool_calls(llm_output)
            
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
            
            
        