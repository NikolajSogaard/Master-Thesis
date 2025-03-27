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
- Address all the feedback provided in the critique and adjust the program based on those suggestions.
- Make sure to adjust the program according to the critique from: frequency and split, exercise selection, set volume, rep ranges, and RPE (Rating of Perceived Exertion).
- You MUST always directly implement all the suggested changes in the program itself from the critique, not just in the suggestion field.
- Maintain the same number of training days unless the feedback explicitly suggests changing it.
Follow this JSON structure as a guide for your response:
{}
'''


# Progressive overload task for Week 2+
TASK_PROGRESSION = '''
Create the next week's training program based on:

1) The previous weeks program programs:
{}

2) The detailed feedback and performance data:
{}

IMPORTANT:
- ONLY modify the "AI Progression" field - keep all exercises, sets, rep ranges and rest periods identical
- Analyze each exercise's performance data (weight, reps, RPE) to create specific recommendations
- For sets completed at/below target RPE: suggest either small weight increases (2.5-5kg) or more reps within the range
- For sets with higher than target RPE: suggest maintaining weight or small decreases
- Include specific numbers in every recommendation (e.g., "Try 82.5kg for 3×8" or "Stay at 60kg but aim for 10-12 reps")
- Address any specific feedback the user provided for individual exercises

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
      },
      {
        "name": "Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": 7-8,
        "rest": "2 minutes",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)",
      },
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
        "AI Progression": "For week 2+, include specific recommendations based on previous week's performance (e.g., 'Based on your performance, try 135kg for 3x8 at RPE 8')"
      },
      {
        "name": "Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": 7-8,
        "rest": "60-90 seconds",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)",
        "AI Progression": "For week 2+, include specific recommendations based on previous week's performance (e.g., 'Based on your performance, try 135kg for 3x8 at RPE 8')"
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
        "AI Progression": "For week 2+, include specific recommendations based on previous week's performance (e.g., 'Increase weight by 5kg to 222kg for 4x6 at RPE 7-8')"
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
    'content': 'You are an AI system specialized adjustion strength training programs based on previous weeks performance' 
                'Your task is to analyze previous performance data and provide specific progression recommendations. '
                'ONLY provide specific weight and effort suggestions in the "AI Progression" field. KEEP the rest of the program identical to the previous week.'
                'Analyze the actual performance (weights, reps achieved, RPE reported) to make data-driven decisions. '
                'Be specific with weight in kg or rep recommendations and explain your reasoning briefly.'
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

# Week 2+ progression - should use task_progression, not task_revision
WRITER_PROMPT_SETTINGS['progression'] = WriterPromptSettings(
    role=PROGRESSION_ROLE,
    task_progression=TASK_PROGRESSION,  # Changed from task_revision to task_progression
    structure=PROGRAM_STRUCTURE_WEEK2PLUS,
)

# Add the original v1 as an alias to initial for backward compatibility
WRITER_PROMPT_SETTINGS['v1'] = WRITER_PROMPT_SETTINGS['initial']
