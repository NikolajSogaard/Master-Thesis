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
For an individual who provided the following input:
{}
Provide feedback if any... otherwise only return "None"
'''

CRITIC_PROMPT_SETTINGS: dict[str, CriticPromptSettings] = {}
CRITIC_PROMPT_SETTINGS['v1'] = CriticPromptSettings(
    role={
        'role': 'system',
        'content': (
            'You are an experienced strength and conditioning coach with deep expertise in exercise science and program design. '
            'Your task is to critically evaluate the training program provided above, considering factors such as safety, effectiveness, '
            'exercise selection, and overall balance. Provide clear, actionable, and evidence-based feedback to help improve the program. '
            'If the program meets all criteria, simply return "None".'
        ),
    },
    task=TASK,
)

