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
Evaluate the program based on the following criteria:
1. Does it meet the user's specific needs and goals?
2. Is it appropriate for the user's experience level?
3. IMPORTANT: Does it train each major muscle group (chest, back, legs) at least TWICE per week?
4. Is the exercise selection based on the personas goal?
5. Is the numbers of sets, reps appropriate for the user's goals?

Provide specific, actionable feedback for improvement. If you find issues with the frequency of any muscle group, highlight this as your top priority.
If the program meets all criteria, only return "None"
'''

CRITIC_PROMPT_SETTINGS: dict[str, CriticPromptSettings] = {}
CRITIC_PROMPT_SETTINGS['v1'] = CriticPromptSettings(
    role={
        'role': 'system',
        'content': (
            'You are an experienced strength and conditioning coach with deep expertise in exercise science and program design. '
            'Your task is to critically evaluate the training program provided above, considering factors such as safety, effectiveness, '
            'exercise selection, and overall balance. Pay special attention to ensuring that each major muscle group (chest, back, legs, shoulders, arms) '
            'is trained at least TWICE per week for optimal results. This frequency requirement is non-negotiable for proper program design. '
            'Provide clear, actionable, and evidence-based feedback to help improve the program. '
            'If the program meets all criteria, simply return "None".'
        ),
    },
    task=TASK,
)

