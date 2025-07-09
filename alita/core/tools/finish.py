from alita.core.tools.finish_observations import FinishObservation
from alita.core.utils import register_function

@register_function
def finish(message: str, task_completed: str) -> FinishObservation:
    """    
    Description: Signals the completion of the current task or conversation.

    Use this tool when:
    - You have successfully completed the user's requested task
    - You cannot proceed further due to technical limitations or missing information

    The message should include:
    - A clear summary of actions taken and their results
    - Any next steps for the user
    - Explanation if you're unable to complete the task
    - Any follow-up questions if more information is needed

    The task_completed field should be set to True if you believed you have completed the task, and False otherwise.

    Parameters:
    (1) message (string, required): Final message to send to the user
    (2) task_completed (string, required): Whether you have completed the task.
    Allowed values: [`true`, `false`, `partial`]
    """

    return FinishObservation(content=message, task_completed=task_completed)
        