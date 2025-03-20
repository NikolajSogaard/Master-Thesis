import dataclasses
from typing import Optional


@dataclasses.dataclass
class WriterPromptSettings:
    role: dict[str, str]
    structure: str
    task: Optional[str] = None
    task_revision: Optional[str] = None
    task_progression: Optional[str] = None

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
- Make sure your program matches the user's experience level, goals, available training time, and any specific information they've provided. Create a personalized program that directly addresses their needs.
- Make sure your program provides sufficient frequency for each major muscle group: chest, back, legs (posterior anterior chain).
- Pick exercises for the individual's goals and needs (hypertrophy, strength, etc.), what order the exercises are placed, and consider set-volume for a whole week.
'''

# Revision task based on critic feedback
TASK_REVISION = '''
Revise the program below:
{}

Based on feedback from your colleague below:
{}

IMPORTANT: 
- You MUST always directly implement all the suggested changes in the program itself from the critique, not just in the suggestion field. This means adjust the program according to the critique from: frequency and split, exercise selection, rep ranges, and RPE (Rating of Perceived Exertion). For example, if feedback says to increase RPE from 7 to 8-9, you should change the actual target_rpe value on that exercise in the program.
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
        "name": "A1: Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": 7-8,
        "rest": "60-90 seconds",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)",
      },
      {
        "name": "B1: Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": 7-8,
        "rest": "0 seconds - superset with B2",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)",
      },
      {
        "name": "B2: Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": 7-8,
        "rest": "60-90 seconds",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)",
      }
    ],
    "Day 2": [
      {
        "name": "A1: Exercise name",
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
        "name": "A1: Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": 7-8,
        "rest": "60-90 seconds",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)",
        "suggestion": "For week 2+, include specific recommendations based on previous week's performance (e.g., 'Based on your performance, try 135kg for 3x8 at RPE 8')"
      },
      {
        "name": "B1: Exercise name",
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
        "name": "A1: Exercise name",
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

# Specific role for initial program creation
INITIAL_WRITER_ROLE = {
    'role': 'system',
    'content': 'You are an AI system specialized in creating initial strength training programs, with expertise in exercise science.' 
                'Your task is to create effective and evidence-based strength training programs tailored to the user’s needs, goals, and experience level. '
                'Focus on establishing the right training frequency, training split, weekly set volume, and exercise selection for the users exerpience level '
                'Provide clear CONCISE, actionable instructions that are appropriate for the specified experience level and don’t go outside the scope of your tasks.'
}

# Specific role for program revision
REVISION_WRITER_ROLE = {
    'role': 'system',
    'content': 'You are an AI system specialized in revising strength training programs based on feedback, with expertise in exercise science.' 
                'Your task is to implement specific feedback and improvements to existing training program.'
                'Focus on addressing weaknesses identified by critics while maintaining program coherence. '
                'Always ensure changes are evidence-based and maintain the program\'s overall structure unless explicitly required to change it.'
                'Provide clear CONCISE adjustments that directly address the feedback given.' 
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

# Initial program creation settings - only has TASK_INITIAL with its own role
WRITER_PROMPT_SETTINGS['initial'] = WriterPromptSettings(
    role=INITIAL_WRITER_ROLE,
    task=TASK_INITIAL,
    structure=PROGRAM_STRUCTURE_WEEK1,
)

# Revision based on critic feedback - only has TASK_REVISION with its own role
WRITER_PROMPT_SETTINGS['revision'] = WriterPromptSettings(
    role=REVISION_WRITER_ROLE,
    task_revision=TASK_REVISION,
    structure=PROGRAM_STRUCTURE_WEEK1,
)

# Week 2+ progression - needs to use task_revision, not task_progression
WRITER_PROMPT_SETTINGS['progression'] = WriterPromptSettings(
    role=PROGRESSION_ROLE,
    task_revision=TASK_PROGRESSION,  # Changed from task_progression to task_revision
    structure=PROGRAM_STRUCTURE_WEEK2PLUS,
)

# Add the original v1 as an alias to initial for backward compatibility
WRITER_PROMPT_SETTINGS['v1'] = WRITER_PROMPT_SETTINGS['initial']
