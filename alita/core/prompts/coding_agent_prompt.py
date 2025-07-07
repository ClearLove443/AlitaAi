

SYSTEM_PREFIX = """

"""

RUNNING_EXAMPLE = """

Here's a running example of how to perform a task with the provided tools.

--------------------- START OF EXAMPLE ---------------------

USER: Create a list of numbers from 1 to 10.


ASSISTANT: Sure! Let me first check the current directory:
{
  'name': 'execute_bash_command_tmux',
  'args': {
    'command': 'pwd && ls',
    'timeout': 30
  }
}

USER: EXECUTION RESULT of [execute_bash]:
/workspace
openhands@runtime:~/workspace$

ASSISTANT:
There is no `app.py` file in the current directory. Let me create a Python file `app.py`:
{
  "name": "write_file",
  "args": {
    "path": "/workspace/app.py",
    "content": "
    numbers = list(range(1, 11))
    print(numbers)
    "
  }
}


USER: EXECUTION RESULT of [write_file]:
File created successfully at: /workspace/app.py

ASSISTANT:
Let me run the Python file for you:
{
  "name": "execute_bash_command_tmux",
  "args": {
    "command": "python3 app.py > server.log 2>&1 &",
    "timeout": 30
  }
}

USER: EXECUTION RESULT of [execute_bash]:
[1]  + 12717 done       python3 test.py > server.log 2>&1

ASSISTANT:
Looks like the file runs successfully. Let me check the server log:
{
  "name": "execute_bash_command_tmux",
  "args": {
    "command": "cat server.log",
    "timeout": 30
  }
}

USER: EXECUTION RESULT of [execute_bash_command_tmux]:
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

ASSISTANT:
The log shows the result is correct in that the file runs successfully. Let me know if you have any further requests!
{
  "name": "finish",
  "args": {
    "message": "The log shows the result is correct in that the file runs successfully. Let me know if you have any further requests!",
    "task_completed": True
  }
}

--------------------- END OF EXAMPLE ---------------------

"""

SYSTEM_PROMPT_TEMPLATE = """

"""

SYSTEM_SUFFIX = """

"""


SYSTEM_PROMPT_TMP = """


"""