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


# Initial program creation task
TASK_INITIAL = '''
Create the best strength training program with a fitting frequency, training split, and numbers of training days, based on this input:
{}

Follow this JSON structure as a guide for your response. The Editor will handle any formatting issues:
{}

Important: 
- Make sure your program matches the persona's experience level, goals, available training time, and any specific information they've provided. Create a personalized program that directly addresses their needs.
- Make sure your program provides sufficient frequency for each major muscle group (each major muscle group should typically be trained at least twice per week for optimal hypertrophy).
- Include appropriate exercise selection for the individual's goals (hypertrophy, strength, etc.).
'''

# Revision task based on critic feedback
TASK_REVISION = '''
Revise the program below:
{}

Based on feedback from your colleague below:
{}

IMPORTANT: 
- You MUST directly implement all the suggested changes in the program itself, not just in the suggestion field. For example, if feedback says to increase RPE from 7 to 8-9, you should change the actual target_rpe value in the exercise.
- Maintain the same number of training days unless the feedback explicitly suggests changing it.

Follow this JSON structure as a guide for your response:
{}
'''

# Progressive overload task for Week 2+
TASK_PROGRESSION = '''
Create the next week's training program based on:

1) The previous program structure:
{}

2) The detailed feedback and performance data:
{}

IMPORTANT:
- Use the same overall program structure (days, split) as the previous week.
- Apply appropriate progressive overload based on the performance data.
- Include personalized 'suggestion' fields for EACH exercise with SPECIFIC numbers for weights (in kg), reps and RPE targets.
- For exercises where the user achieved their target RPE and completed all prescribed reps, increase the load appropriately.
- For exercises where the user struggled (higher than target RPE or failed to complete reps), adjust accordingly.
- If the user provided specific feedback for an exercise, address it directly in your updated programming.

Follow this JSON structure as a guide for your response:
{}
'''

PROGRAM_STRUCTURE_WEEK1 = '''
{
  "weekly_program": {
    "Day 1": [
      {
        "name": "Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": 7-8,
        "rest": "60-90 seconds",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)",
      }
    ],
    "Day 2": [
      {
        "name": "Exercise name",
        "sets": 4,
        "reps": "5-8",
        "target_rpe": 8-10,
        "rest": "2-3 minutes",
        "cues": "Brief note from AI about form, focus points, or exercise purpose (keep it short)",
      }
    ],
    "Day X": etc. continue generating each training day of the week.
  }
}
'''

PROGRAM_STRUCTURE_WEEK2PLUS = '''
{
  "weekly_program": {
    "Day 1": [
      {
        "name": "Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": 7-8,
        "rest": "60-90 seconds",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)",
        "suggestion": "For week 2+, include specific recommendations based on previous week's performance (e.g., 'Based on your performance, try 135kg for 3x8 at RPE 8')"
      }
    ],
    "Day 2": [
      {
        "name": "Exercise name",
        "sets": 4,
        "reps": "5-8",
        "target_rpe": 8-10,
        "rest": "2-3 minutes",
        "cues": "Brief note from AI about form, focus points, or exercise purpose (keep it short)",
        "suggestion": "For week 2+, include specific recommendations based on previous week's performance (e.g., 'Increase weight by 5lkg to 222kg for 4x6 at RPE 7-8')"
      }
    ],
    "Day X": etc. continue generating each training day of the week.
  }
}
'''

# Base role for writers
WRITER_ROLE = {
    'role': 'system',
    'content': 'You are an AI system specialized in creating personalized strength training programs.' 
                'You have expertise in exercise science, biomechanics, and training periodization. '
                'Your task is to create effective, and evidence-based strength training programs tailored to the user\'s needs, goals, and experience level. '
                'Always prioritize proper progression, and training variety. '
                'Provide clear CONCISE, actionable instructions that are appropriate for the specified experience level.'
}

# Enhanced role for progression writer
PROGRESSION_ROLE = {
    'role': 'system',
    'content': 'You are an AI system specialized in creating personalized strength training programs with a focus on progression.' 
                'You have expertise in exercise science, biomechanics, and training periodization. '
                'Your task is to create effective, evidence-based training progressions based on previous performance data. '
                'Analyze the actual performance (weights, reps achieved, RPE reported) to make data-driven decisions for the next training week. '
                'Be specific with weight recommendations and progression strategies. '
                'Provide clear, actionable instructions that are appropriate for the specified experience level.'
}

# Dictionary to store all prompt settings
WRITER_PROMPT_SETTINGS: dict[str, WriterPromptSettings] = {}

# Initial program creation settings
WRITER_PROMPT_SETTINGS['initial'] = WriterPromptSettings(
    role=WRITER_ROLE,
    task=TASK_INITIAL,
    task_revision=TASK_REVISION,  # Not typically used for initial
    structure=PROGRAM_STRUCTURE_WEEK1,
)

# Revision based on critic feedback
WRITER_PROMPT_SETTINGS['revision'] = WriterPromptSettings(
    role=WRITER_ROLE,
    task=TASK_INITIAL,  # Included as fallback
    task_revision=TASK_REVISION,
    structure=PROGRAM_STRUCTURE_WEEK1,
)

# Week 2+ progression
WRITER_PROMPT_SETTINGS['progression'] = WriterPromptSettings(
    role=PROGRESSION_ROLE,
    task=TASK_INITIAL,  # Included as fallback
    task_revision=TASK_PROGRESSION,
    structure=PROGRAM_STRUCTURE_WEEK2PLUS,
)

# Add the original v1 as an alias to initial for backward compatibility
WRITER_PROMPT_SETTINGS['v1'] = WRITER_PROMPT_SETTINGS['initial']
