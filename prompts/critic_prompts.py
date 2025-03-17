import dataclasses
from typing import Dict, Optional

@dataclasses.dataclass
class CriticPromptSettings:
    role: dict[str, str]
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

For strength/powerlifting-focused goals, consider:
- Full body with main lift focus (3-4x/week): Each session focuses on one main lift (squat, bench, deadlift) with higher frequency
- Upper/Lower (4x/week): With frequency for main lifts 2-3x per week
- Push/Pull/Legs with main lift priority (4-6x/week): Main lifts can appear 2-4x per week with varied intensity
- Specialized split like the Sheiko approach or Daily Undulating Periodization (DUP) where main lifts are trained 3-4x per week

For powerlifting/strength goals, the frequency of specific main lifts (for example: squat, bench, deadlift) is often MORE important than the frequency of muscle groups. Main lifts can be trained 2-4 times per week with proper load management.
IMPORTANT:
- Main lift can also be alternative variations like front squat, incline bench press, or Romanian deadlift. I it dont nessesary have to have only one of these main lifts or variations each training day.

If the training frequency or split needs improvement, provide specific recommendations that better match the user's goals and available training days.

Provide feedback if any... otherwise only return "None"
'''


TASK_EXERCISE_SELECTION = '''
Your colleague has written the following training program:
{}

The individual has provided these details:
{}

Focusing **only** on EXERCISE SELECTION.
Check if the chosen exercises align with the person’s stated goals and experience level and look for exercises preferences That the user might prefer.


For hypertrophy-focused goals, have this in mind:
- For bodybuilding/hypertrophy goals, confirm a balanced mix of compound and isolation exercises. Go somewhere between 50 to 70 percent compound exercises and 30 to 50 percent isolation exercises. 
- The programs should be bodybuilding focused, with a variety of exercises to target each muscle group from different angles.
- 50-50 procent mix of free-weight and machine exercises. 

For strength/powerlifting-focused goals, consider:
- For powerlifting/strength goals, ensure frequent emphasis on squat, bench press, and deadlift.
Provide constructive feedback if any changes are needed. If there is nothing to improve, return "None".
=======
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

The individual has provided these details:
{}

Focus ONLY on the REP RANGES:
- Check if they align with the individual’s goals.
- For compound exercises (like squat or deadlift), use 5–8 reps.
- For isolation exercises, use 5–20 reps.
- Do not include AMRAP (As Many Reps As Possible).

Provide constructive feedback if any changes are needed. If there is nothing to improve, return "None".'''


TASK_RPE = '''
Your colleague has written the following training program:
{}

The individual has provided these details:
{}

Focus ONLY on the RPE (Rating of Perceived Exertion) Targets:
- Check if the RPE values are appropriate for the individual’s experience level.
- Isolation exercises should have a higher Target RPE (8–10).
- Compound movements should have a slightly lower Target RPE.

Provide constructive feedback on any needed changes. 
If there are no issues, respond with "None".'''


TASK_PROGRESSION = '''
Your colleague has written the following training program:
{}

The individual has provided these details:
{}

Focus ONLY on the PROGRESSION aspect of the program:
- Check if a clear method of progressive overload is incorporated (e.g., increasing weight, reps, or difficulty over time).
- Verify that the progression strategy matches the individual’s experience level (e.g., straightforward linear progression for beginners; more nuanced approaches for intermediate/advanced).
- Consider the frequency of progression and whether it’s realistic and safe for the stated goals.

Provide concise feedback if any improvements are needed. 
If there are no issues, respond with "None".
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

