import dataclasses


@dataclasses.dataclass
class CriticPromptSettings:
    role: dict[str, str]
    task: str

    def save(self, fname: str):
        raise NotImplementedError

    def load(self, fname: str):
        raise NotImplementedError


# Make sure to read writer_prompts.py first!
TASK = '''
Your colleague has written the following training program:
{}
For an individial who provided the following input
{}
Provide feedback if any... otherwise only return "None"
'''

CRITIC_PROMPT_SETTINGS: dict[str, CriticPromptSettings] = {}
CRITIC_PROMPT_SETTINGS['v1'] = CriticPromptSettings(
    role={
        'role': 'system',
        'content': '......', # You are a helpful.....
    },
    task=TASK,
)
