import dataclasses
from typing import Dict, Optional, List

# Define reusable prompt components
COMMON_RESPONSE_FORMAT = '''
IMPORTANT: 
1. Provide SPECIFIC, CONCRETE suggestions - don't just identify problems
2. For each change, specify exactly what to modify and how
3. If nothing needs improvement, return "None"
'''

@dataclasses.dataclass
class PromptComponent:
    """Reusable components for building prompts"""
    intro: str
    evaluation_criteria: List[str]
    guidelines: Dict[str, List[str]]
    action_instructions: List[str]
    response_format: str = COMMON_RESPONSE_FORMAT

    def format_for_task(self, task_type: str) -> str:
        """Format the component for a specific task type"""
        criteria = "\n".join([f"{i+1}. {c}" for i, c in enumerate(self.evaluation_criteria)])
        
        # Only include guidelines relevant to this task
        guidelines_text = ""
        if task_type in self.guidelines:
            guidelines = self.guidelines[task_type]
            guidelines_text = "\nGuidelines:\n" + "\n".join([f"- {g}" for g in guidelines])
        
        actions = "\n".join([f"- {a}" for a in self.action_instructions])
        
        return f"{self.intro}\n\nEvaluate whether:\n{criteria}\n{guidelines_text}\n\nIMPORTANT ACTIONS:\n{actions}\n{self.response_format}"

@dataclasses.dataclass
class CriticPromptSettings:
    role: dict[str, str]
    tasks: Optional[Dict[str, str]] = None  # Dictionary of task templates by type

TASK_FREQUENCY_AND_SPLIT = '''
Your colleague has written the following training program:
{}
For an individual who provided the following input:
{}
Focus ONLY on the TRAINING FREQUENCY and SPLIT SELECTION. Do NOT comment on exercise selection, rep ranges, or RPE.

Specifically, evaluate whether:
1. The program provides sufficient frequency for each major muscle group
2. The training split effectively utilizes the user's available training days
3. The split is appropriate for the user's goals (strength, powerlifting, hypertrophy, beginners etc.)

For hypertrophy-focused goals, consider these common split options:
- Full body (2x/week): Trains all muscle groups each session
- hybrid full body (3x/week): Alternates between full body and upper/lower splits
- Upper/Lower (4x/week): Alternates between upper and lower body days
- Hybrid splits (5 days): Such as Push, Pull, Legs, Upper, Lower
- Push/Pull/Legs (6x/week): One day each for pushing movements, pulling movements, and leg exercises

For powerlifting and strength-focused goals, consider these specialized split options:
- Movement-based splits: Organize training around the individual's main lifts, not necessarily traditional powerlifts
- Conjugate/Westside approach: Max effort days and dynamic effort days for upper and lower body
- Upper/Lower with specialized days: Focus days built around the individual's primary movements
- Main lift + supplemental work: Each day features one main compound lift followed by related assistance work

For strength and powerlifting goals, consider the following recommendations:
- Prioritize Main Lifts: Focus on the individual's preferred main exercises—these might be traditional lifts like squat, bench press, and deadlift, or could be alternatives like hack squats, pull-ups, dips, or overhead press, depending on the individual's preferences and training history.
- Higher Frequency for Main Lifts: The individual's main lifts and their variations can be trained more than two times per week with proper load management.
- Accessory Work: Although main lifts receive higher frequency, accessory exercises should be performed less frequently.
- Tailored Adjustments: If the current training frequency or split doesn't align with the user's available training days or specific goals, adjust the plan to better match those needs.
- Specialized Training Days: It's appropriate to have specialized days (like "posterior chain focus") as long as overall weekly volume remains balanced across muscle groups/movement patterns.

IMPORTANT: If changes are needed, provide SPECIFIC, CONCRETE suggestions - specify exactly what split structure you recommend with a clear layout of training days.
If nothing needs improvement, return "None".
'''

TASK_EXERCISE_SELECTION = '''
Your colleague has written the following training program:
{}

The individual has provided these details:
{}

Focus ONLY on EXERCISE SELECTION. Do NOT comment on frequency, split structure, rep ranges, or RPE.

Evaluate whether:
- The chosen exercises align with the individual's goals, experience level, and personal preferences
- NOTE: If the frequency_and_split critique suggested different training splits or structure, consider how exercises would fit into that revised structure rather than the original

For hypertrophy-focused goals:
- Maintain a balanced mix of compound (50-70%) and isolation (30-50%) exercises
- Include a variety of exercises to target each muscle group from different angles
- Aim for a 50-50 mix of free-weight and machine exercises

For strength/powerlifting-focused goals:
- Choose exercises that directly complement the individual's main lifts or their well-suited variations
- Main lifts should be based on the individual's preferences and goals, not necessarily traditional powerlifts
- For powerlifting programs, structure each day around 1-2 main compound movements followed by relevant accessories
- It's acceptable to place certain "main" lifts on seemingly unrelated days (e.g., pull-ups on leg day) if:
  1. It serves a specific purpose (e.g., back development for improved bracing on squats)
  2. It doesn't interfere with recovery for the primary focus of that day
  3. The overall weekly volume and frequency for that movement pattern is appropriate
- Identify accessory movements that target the supporting muscle groups impacting the main lifts
- For specialized days (like posterior chain focus), ensure that across the week, all muscle groups and movement patterns receive balanced attention

Balance considerations for specialized training days:
- When creating a specialized day (e.g., posterior chain focus), compensate with complementary work on other days
- Ensure appropriate opposing muscle group work within the week (e.g., if emphasizing hamstrings heavily, ensure adequate quad work elsewhere)
- Main lifts should be placed where recovery will be optimal for performance

IMPORTANT: If changes are needed, provide SPECIFIC, CONCRETE suggestions - list exactly which exercises to replace and what to replace them with.
If nothing needs improvement, return "None".
'''

TASK_SET_VOLUME = '''
Your colleague has written the following training program:
{}

The individual has provided these details:
{}

Focus ONLY on evaluating the WEEKLY SET VOLUME for each major muscle group and suggesting concrete adjustments. Do NOT comment on frequency, split structure, exercise selection specifics, rep ranges, or RPE.

NOTE: Consider any changes suggested by previous critiques (frequency_and_split, exercise_selection) when evaluating set volume.

1) First, calculate the current weekly volume for:
   - Chest
   - Back
   - Legs

2) Then, evaluate if the volume needs to be changed based on these evidence-based guidelines:
   - Beginners: 10-12 weekly sets per major muscle group
   - Intermediates: 13-18 weekly sets per major muscle group
   - Advanced: 16-20+ weekly sets per major muscle group
   - Small muscle groups: 30-40% fewer sets than major muscle groups

   From the reference table (major muscle groups only):
   - Back:
     • Beginner: 8–10 sets
     • Intermediate: 10–20 sets
   - Chest:
     • Beginner: 8–10 sets
     • Intermediate: 10-15 sets
   - Glutes:
     • Intermediate: 10–20 sets
   - Hamstrings:
     • Beginner: 6–10 sets
     • Intermediate: 8–12 sets
   - Quads:
     • Beginner: 8–10 sets
     • Intermediate: 10–15 sets
   - Shoulders:
     • Intermediate: 10–20 sets



3) IMPORTANT: Make CONCRETE ADJUSTMENTS to the program while ensuring proper volume distribution throughout the week:
   - If volume is too high: Either reduce the number of sets for specific exercises OR completely remove certain exercises. Specify exactly which exercises to modify and from which days
   - If volume is too low: Either increase the number of sets for existing exercises OR add new exercises. Specify exactly which exercises to modify or add, with specific set/rep recommendations
   - If muscle group balance is off: Identify which muscle groups are overemphasized or underemphasized, then suggest specific exercises to add, remove, or modify numbers of sets to create proper balance. Specify exactly which adjustments to make on which training days
   - Ensure volume for each muscle group is distributed appropriately across multiple training days rather than concentrated on a single day
   - IMPORTANT: 
        - When suggesting a range of sets (e.g., 10-12 sets per week), ALWAYS start at the lower end of the range
        - The number of sets of an exercise should be inbetween 2-5 sets.
        - Compound exercise can be a part of the volume of multiple muscle groups.

Do not just analyze - actually modify the program to create optimal training volume with proper distribution throughout the week.
If the volume distribution is already optimal, return "None".
'''



TASK_REP_RANGES = '''
Your colleague has written the following training program:
{}

The individual has provided these details:
{}

Focus ONLY on the REP RANGES. Do NOT comment on frequency, split structure, exercise selection, or RPE.

Evaluate whether:
- The rep ranges align with the individual's goals
- NOTE: Consider any changes suggested by previous critiques (frequency_and_split, exercise_selection, set_volume) when evaluating rep ranges
- Make sure your rep range recommendations work with the training split exercise selection, and volume recommendations

Guidelines:
- For compound exercises (like squat or deadlift), use lower rep-ranges like 5–8 reps
- For isolation exercises, use higher rep-ranges like 8-15 reps
- Do not include AMRAP (As Many Reps As Possible)

IMPORTANT: If changes are needed, provide SPECIFIC, CONCRETE suggestions - specify exact rep ranges for each exercise that needs adjustment.
If nothing needs improvement, return "None".
'''

TASK_RPE = '''
Your colleague has written the following training program:
{}

The individual has provided these details:
{}

Focus ONLY on the RPE (Rating of Perceived Exertion) Targets. Do NOT comment on frequency, split structure, exercise selection, or rep ranges.

Evaluate whether:
- The RPE values are appropriate for the individual's experience level
- NOTE: Consider any changes suggested by ALL previous critiques (frequency_and_split, exercise_selection, set_volume, rep_ranges) when evaluating RPE targets
- Your RPE recommendations should be compatible with the training frequency, exercise selection, set volume, and rep ranges previously recommended

Guidelines:
- Isolation exercises should have a higher Target RPE 8–10
- Compound movements should have a slightly lower Target RPE
- Always provide the RPE in a range (e.g., 8-9, 9-10)
- Exercises that require lower stability (like machine exercises, or something like cable flies) could use a high RPE (8-10)

IMPORTANT: If changes are needed, provide SPECIFIC, CONCRETE suggestions - specify exact RPE targets for each exercise that needs adjustment.
If nothing needs improvement, return "None".
'''

TASK_PROGRESSION = '''
Your colleague has written the following Week {week_number} training program:
{}

The individual provided this input for their original program:
{}

Here is the performance data from the previous week:
{}

Focus ONLY on PROGRESSION & PROGRESSIVE OVERLOAD.

Evaluate whether:
1. The program effectively applies progressive overload based on previous week's performance:
   - The exercise weights/loads are appropriate based on actual performance
   - The suggested progression rates are realistic and evidence-based
   - The RPE targets match the individual's demonstrated performance capacity

2. The program includes:
   - Appropriate weight increases based on previous week's performance
   - Suitable adjustments to reps, sets, or intensity where needed
   - Progressive overload application that matches the individual's training experience
   - Specific, actionable suggestions in the "suggestion" field for each exercise

3. The program effectively:
   - Builds on strengths demonstrated in previous performance data
   - Addresses weaknesses or sticking points from previous week
   - Applies proper autoregulation principles based on RPE feedback

IMPORTANT: Provide SPECIFIC, CONCRETE suggestions with exact numbers - specify precise weight adjustments (in kg), rep changes, and RPE targets for exercises needing modification.
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
        'set_volume': TASK_SET_VOLUME,
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
for setting_key in ['frequency_and_split', 'exercise_selection', 'set_volume', 'rep_ranges', 'rpe']:
    if setting_key in CRITIC_PROMPT_SETTINGS:
        task_var_name = f"TASK_{setting_key.upper()}"
        task_template = locals().get(task_var_name, globals().get(task_var_name))
        CRITIC_PROMPT_SETTINGS[setting_key].tasks = {
            'frequency_and_split': TASK_FREQUENCY_AND_SPLIT,
            'exercise_selection': TASK_EXERCISE_SELECTION,
            'set_volume': TASK_SET_VOLUME,
            'rep_ranges': TASK_REP_RANGES,
            'rpe': TASK_RPE,
        }

