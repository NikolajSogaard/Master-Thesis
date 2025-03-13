import dataclasses
from typing import Dict, Optional

@dataclasses.dataclass
class CriticPromptSettings:
    role: dict[str, str]
    task: Optional[str] = None  # Single task for backward compatibility
    tasks: Optional[Dict[str, str]] = None  # Dictionary of task templates by task type


TASK_EXERCISE_SELECTION = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}
Focus specifically on the EXERCISE SELECTION. Are the exercises appropriate for this individual's goals, level, and any limitations?
Provide feedback if any... otherwise only return "None"
'''

TASK_REP_RANGES = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}
Focus specifically on the REP RANGES. Are they optimal for the stated training goals?
For compound exercises like squat and deadlift, use a REP RANGES of 5-8.
For isolation exercises use a REP RANGES of 5-20. 
Provide feedback if any... otherwise only return "None"
'''

TASK_RPE = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}
Focus specifically on the RPE (Rating of Perceived Exertion) TARGETS. Are they appropriate for this individual's experience level?
Consider whether the intensity aligns with the the specific exercise.
Isolation exercises should have higher Target RPE (8-10). Compound movements should have a little lower.
Provide feedback if any... otherwise only return "None"
'''

TASK_PROGRESSION = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}
Focus specifically on PROGRESSION. Does the program incorporate appropriate progressive overload principles?
Provide feedback if any... otherwise only return "None"
'''

# Dictionary of specialized critic settings for different evaluation tasks
CRITIC_PROMPT_SETTINGS: dict[str, CriticPromptSettings] = {}

# Update the CRITIC_PROMPT_SETTINGS to include all task templates
CRITIC_PROMPT_SETTINGS['v1'] = CriticPromptSettings(
    role={
        'role': 'system',
        'content': (
            'You are an experienced strength and conditioning coach with deep expertise in exercise science and program design.'
            'Your task is to critically evaluate the training program provided above, considering factors such as safety, effectiveness, exercise selection, and overall balance.' 
            'Provide clear, actionable, and evidence-based feedback to help improve the program.'
            'If the program meets all criteria, simply return "None".'
        ),
    },
    # Keep original task for backward compatibility
    task=TASK_EXERCISE_SELECTION,
    # Add all tasks
    tasks={
        'exercise_selection': TASK_EXERCISE_SELECTION,
        'rep_ranges': TASK_REP_RANGES,
        'rpe': TASK_RPE,
        'progression': TASK_PROGRESSION,
    },
)

# Update other settings to include all tasks
for setting_key in ['exercise_selection', 'rep_ranges', 'rpe', 'progression']:
    if setting_key in CRITIC_PROMPT_SETTINGS:
        task_var_name = f"TASK_{setting_key.upper()}"
        task_template = locals().get(task_var_name, globals().get(task_var_name))
        CRITIC_PROMPT_SETTINGS[setting_key].tasks = {
            'exercise_selection': TASK_EXERCISE_SELECTION,
            'rep_ranges': TASK_REP_RANGES,
            'rpe': TASK_RPE,
            'progression': TASK_PROGRESSION,
        }

