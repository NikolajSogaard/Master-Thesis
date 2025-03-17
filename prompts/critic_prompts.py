import dataclasses
from typing import Dict, Optional

@dataclasses.dataclass
class CriticPromptSettings:
    role: dict[str, str]
    task: Optional[str] = None  # Single task for backward compatibility
    tasks: Optional[Dict[str, str]] = None  # Dictionary of task templates by task type

TASK_FREQUENCY_and_SPLIT = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}

Focus specifically on the TRAINING FREQUENCY and SPLIT SELECTION.

Answer the following questions:
1. Does the program provide sufficient frequency for each major muscle group? (Each major muscle group should typically be trained at least twice per week for optimal hypertrophy)
2. Does the training split effectively utilize the user's available training days?
3. Is the split appropriate for the user's goals (strength, hypertrophy, etc.)?

For hypertrophy-focused goals, consider these common split options:
- Full body (2x/week): Trains all muscle groups each session
- hybrid full body (3x/week): Alternates between full body and upper/lower splits
- Upper/Lower (4x/week): Alternates between upper and lower body days
- Hybrid splits (5 days): Such as Push, Pull, Legs, Upper, Lower
- Push/Pull/Legs (6x/week): One day each for pushing movements, pulling movements, and leg exercises

If the training frequency or split needs improvement, provide specific recommendations that better match the user's goals and available training days.

Provide feedback if any... otherwise only return "None"
'''

TASK_EXERCISE_SELECTION = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}
Focus specifically on the EXERCISE SELECTION, and look into the user to see perfered exercise IF any. 
Does the exercises make sence for this individual's goals and level?
Consider these factors:
- For a beginner choose easy to learn exercises that are safe and effective.
- For a bodybuilding program, include a mix of compound and isolation exercises.
- For a powerlifting program, make sure to have a high frequency of the squat, bench press, and deadlift.
Provide feedback if any... otherwise only return "None"
'''

TASK_REP_RANGES = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}
Focus specifically on the REP RANGES. Are they optimal for the stated training goals?
For compound exercises like squat and deadlift, use a lower REP RANGES from 1-8.
For isolation exercises use a REP RANGES of 8-20.
Dont use AMRAP (As Many Reps As Possible).
In general, use REP RANGES in small intervals of 2-3 reps. For example, use 5-8, 8-10, 10-12, 12-15.
Provide feedback if any... otherwise only return "None"
'''

TASK_RPE = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}
Focus specifically on the RPE (Rating of Perceived Exertion) TARGETS. Are they appropriate for this individual's experience level?

Consider these factors:
1. Is the intensity appropriate for each specific exercise?
2. Isolation exercises typically should have higher RPE targets (e.g.,9-10 or 10) compared to compound movements
3. RPE can be expressed as either a single value (e.g., 8) or a range (e.g., 7-8) depending on the exercise and training goal
4. More experienced lifters can generally train at higher RPE values

When providing feedback, be clear about whether RPE values should be absolute numbers or ranges.

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
            'Your task is to critically evaluate the training program provided above, considering factors such as, effectiveness, exercise selection, and overall balance.' 
            'Provide clear, actionable, and evidence-based feedback to help improve the program.'
            'If the program meets all criteria, simply return "None".'
        ),
    },
    # Keep original task for backward compatibility
    task=TASK_EXERCISE_SELECTION,
    # Add all tasks
    tasks={
        'frequency_and_split': TASK_FREQUENCY_and_SPLIT,
        'exercise_selection': TASK_EXERCISE_SELECTION,
        'rep_ranges': TASK_REP_RANGES,
        'rpe': TASK_RPE,
    },
)

# Update other settings to include all tasks
for setting_key in ['frequency_and_split', 'exercise_selection', 'rep_ranges', 'rpe', 'progression']:
    if setting_key in CRITIC_PROMPT_SETTINGS:
        task_var_name = f"TASK_{setting_key.upper()}"
        task_template = locals().get(task_var_name, globals().get(task_var_name))
        CRITIC_PROMPT_SETTINGS[setting_key].tasks = {
            'frequency_and_split': TASK_FREQUENCY_and_SPLIT,
            'exercise_selection': TASK_EXERCISE_SELECTION,
            'rep_ranges': TASK_REP_RANGES,
            'rpe': TASK_RPE,
        }

