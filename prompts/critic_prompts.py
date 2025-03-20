import dataclasses
from typing import Dict, Optional

@dataclasses.dataclass
class CriticPromptSettings:
    role: dict[str, str]
    tasks: Optional[Dict[str, str]] = None  # Dictionary of task templates by task type


TASK_FREQUENCY_AND_SPLIT = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}
Focus specifically on the TRAINING FREQUENCY and SPLIT SELECTION.
Consider if:
1. The program provide sufficient frequency for each major muscle group (Each major muscle group should typically be trained at least twice per week for optimal hypertrophy)
2. The training split effectively utilize the user's available training days.
3. The split appropriate for the user's goals (strength, powerlifting, hypertrophy, beginners etc.)

For hypertrophy-focused goals, consider these common split options:
- Full body (2x/week): Trains all muscle groups each session
- hybrid full body (3x/week): Alternates between full body and upper/lower splits
- Upper/Lower (4x/week): Alternates between upper and lower body days
- Hybrid splits (5 days): Such as Push, Pull, Legs, Upper, Lower
- Push/Pull/Legs (6x/week): One day each for pushing movements, pulling movements, and leg exercises

For strength and powerlifting goals, consider the following recommendations:
- Prioritize Main Lifts: Focus on main exercises—such as squat, bench press, and deadlift—as well as their variations (e.g., front squat, incline bench press, Romanian deadlift). Depending on the user's training persona, these main exercises may also be alternative movements like hack squats, chin-ups, or dips. 
- Higher Frequency for Main Lifts: Main lifts and their variations can be trained more than two times per week with proper load management. Their frequency is often more critical than targeting individual muscle groups.
- Accessory Work: Although main lifts receive higher frequency, accessory exercises should be performed less frequently.
- Tailored Adjustments: If the current training frequency or split doesn't align with the user's available training days or specific goals, adjust the plan to better match those needs.

Provide feedback if any... otherwise only return "None"
'''



TASK_EXERCISE_SELECTION = '''
Your colleague has written the following training program:
{}

The individual has provided these details:
{}

Your task is to find the best fitting exercises for the user.

Focus ONLY on EXERCISE SELECTION:
- Check that the chosen exercises not only align with the individual's goals and experience level but also match their personal preferences.

For hypertrophy-focused goals:
- Maintain a balanced mix of compound (50-70%) and isolation (30-50%) exercises.
- Include a variety of exercises to target each muscle group from different angles.
- Aim for a 50-50 mix of free-weight and machine exercises.

For strength/powerlifting-focused goals:
- Choose exercises that directly complement the user's main lifts (e.g., squat, pull-ups, dips) or their well-suited variations (like front squat/hack squat, lat pulldown narrow grip, or bench press). The selected exercises should be consistent with the user's preferred movement patterns.
- Identify accessory movements that target the supporting muscle groups impacting the main lifts.

Provide constructive feedback if any changes are needed.
If there is nothing to improve, return "None".
'''



TASK_REP_RANGES = '''
Your colleague has written the following training program:
{}

The individual has provided these details:
{}

Focus ONLY on the REP RANGES:
- Check if they align with the individual’s goals.
- For compound exercises (like squat or deadlift), could use lower rep-ranges like 5–8 reps.
- For isolation exercises, could use higher rep-ranges like 8-15 reps.
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
- Exercises that require lower stability (like machine exercises, or something like cable flies) could use a high RPE (8-10).

Provide constructive feedback if any changes are needed. If there is nothing to improve, return "None".'''

TASK_PROGRESSION = '''
Your colleague has written the following Week {week_number} training program:
{}

The individual provided this input for their original program:
{}

Here is the performance data from the previous week:
{}

Focus ONLY on PROGRESSION & PROGRESSIVE OVERLOAD:

1. Analyze the performance data from the previous week to determine if:
   - The exercise weights/loads are appropriate based on actual performance
   - The suggested progression rates are realistic and evidence-based
   - The RPE targets match the individual's demonstrated performance capacity

2. Check for specific progression elements:
   - Appropriate weight increases based on previous week's performance
   - Suitable adjustments to reps, sets, or intensity where needed
   - Progressive overload application that matches the individual's training experience
   - Specific, actionable suggestions in the "suggestion" field for each exercise

3. Verify that the program effectively:
   - Builds on strengths demonstrated in previous performance data
   - Addresses weaknesses or sticking points from previous week
   - Applies proper autoregulation principles based on RPE feedback

Provide detailed, specific feedback with concrete recommendations on weights, reps, and RPE targets where appropriate.
Only return "None" if the progression strategy is already optimal.
'''

# Dictionary of specialized critic settings for different evaluation tasks
CRITIC_PROMPT_SETTINGS: dict[str, CriticPromptSettings] = {}

# Update the CRITIC_PROMPT_SETTINGS to include Week 1 tasks (without progression)
CRITIC_PROMPT_SETTINGS['week1'] = CriticPromptSettings(
    role={
        'role': 'system',
        'content': (
            'You are an experienced strength training coach with deep expertise in exercise science and program design.'
            'Your job is to critically evaluate the training program provided above, for the task provided' 
            'Provide clear, actionable, feedback to help improve the program.'
            'If the program meets all criteria, simply return "None".'
        ),
    },
    tasks={
        'frequency_and_split': TASK_FREQUENCY_AND_SPLIT,
        'exercise_selection': TASK_EXERCISE_SELECTION,
        'rep_ranges': TASK_REP_RANGES,
        'rpe': TASK_RPE,
    },
)

# Setting for Week 2+ with progression focus only
CRITIC_PROMPT_SETTINGS['progression'] = CriticPromptSettings(
    role={
        'role': 'system',
        'content': (
            'You are an experienced strength and conditioning coach with deep expertise in exercise science, program design, and progressive overload principles. '
            'Your task is to analyze the training program and previous week\'s performance data to ensure effective progression and proper autoregulation. '
            'Provide specific, actionable feedback on weight selection, rep ranges, RPE targets, and progression rates. '
            'Make precise recommendations for adjustments to optimize the program for continued progress. '
            'If the program meets all criteria for optimal progression, simply return "None".'
        ),
    },
    tasks={
        'progression': TASK_PROGRESSION,  # Use the single progression task
    },
)

# Update other individual task settings - remove progression from non-progression settings
for setting_key in ['frequency_and_split', 'exercise_selection', 'rep_ranges', 'rpe']:
    if setting_key in CRITIC_PROMPT_SETTINGS:
        task_var_name = f"TASK_{setting_key.upper()}"
        task_template = locals().get(task_var_name, globals().get(task_var_name))
        CRITIC_PROMPT_SETTINGS[setting_key].tasks = {
            'frequency_and_split': TASK_FREQUENCY_AND_SPLIT,
            'exercise_selection': TASK_EXERCISE_SELECTION,
            'rep_ranges': TASK_REP_RANGES,
            'rpe': TASK_RPE,
        }

