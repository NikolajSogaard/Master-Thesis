import dataclasses


@dataclasses.dataclass
class WriterPromptSettings:
    role: dict[str, str]
    task: str
    task_revision: str
    structure: str

    def save(self, fname: str):
        raise NotImplementedError

    def load(self, fname: str):
        raise NotImplementedError


# Ultimately, you'll likely want to extract the text fields outside of Python, but maybe easy to start this way
# You could also implement .save and .load methods as indicated above and use those 
TASK = '''
Create the best program based on the user input below:
{}
Create the program in the following format, making sure to only return valid JSON:
{}
''' # Create training program, etc.
TASK_REVISION = '''
Revise the program below:
{}
Based on feedback from your colleague below:
{}
Make sure the revised progam follows the format below, making sure to only return valid JSON:
{}
'''

PROGRAM_STRUCTURE = '''
{
}
''' # Structure output this way, e.g., some JSON format


WRITER_PROMPT_SETTINGS: dict[str, WriterPromptSettings] = {}
WRITER_PROMPT_SETTINGS['v1'] = WriterPromptSettings(
    role={
        'role': 'system',
        'content': '', # You are an AI system for creating trainign prgrams, etc etc
    },
    task=TASK,
    task_revision=TASK_REVISION,
    structure=PROGRAM_STRUCTURE,
)
# Maybe you make a second version w/ different task, etc.
