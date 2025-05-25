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

1) The previous week's program:
{}

2) The detailed feedback and performance data:
{}

IMPORTANT:
- ONLY modify the "AI Progression" field - keep all exercises, sets, rep ranges and rest periods identical
- YOUR RESPONSE MUST FOLLOW EXACTLY THIS FORMAT FOR LOAD ADJUSTMENTS WITH NO VARIATION:
  Set 1:(8 reps @ 80kg, RPE 7)
  Set 2:(8 reps @ 80kg, RPE 8)
  Set 3:(7 reps @ 80kg, RPE 9)
        75kg ↓

- YOUR RESPONSE MUST FOLLOW EXACTLY THIS FORMAT FOR REP ADJUSTMENTS WITH NO VARIATION:
  Set 1:(8 reps @ 80kg, RPE 7)
  Set 2:(8 reps @ 80kg, RPE 8)
  Set 3:(7 reps @ 80kg, RPE 9)
        10 reps ↑
  
- First line must be "Set 1:" followed by performance data in parentheses "(reps @ weight, RPE score)"
- Include ONE line per set showing the actual performance data from last week
- Then provide ONE line with ONLY the adjustment with arrow symbol - nothing else
- Use "↑" for increases and "↓" for decreases
- For weight changes: "85kg ↑" or "75kg ↓" 
- For rep changes: "10 reps ↑" or "8 reps ↓"
- DO NOT include any other explanatory text whatsoever
- DO NOT include phrases like "Based on your performance" or "Aim for" or "Target RPE"
- DO NOT include any recommendations about RPE targets
- If no performance data is available, leave the suggestion field empty

IMPORTANT: Your AI Progression field must contain ONLY the set data and adjustment line as shown above.

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
        "target_rpe": "7-8",
        "rest": "60-90 seconds",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)"
      },
      {
        "name": "Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": "7-8",
        "rest": "2 minutes",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)"
      },
      {
        "name": "Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": "7-8",
        "rest": "60-90 seconds",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)"
      }
    ],
    "Day 2": [
      {
        "name": "Exercise name",
        "sets": 4,
        "reps": "5-8",
        "target_rpe": "8-10",
        "rest": "2-3 minutes",
        "cues": "Brief note from AI about form, focus points, or exercise purpose (keep it short)"
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
    task_progression=TASK_PROGRESSION,
    structure=None,
)

# Add the original v1 as an alias to initial for backward compatibility
WRITER_PROMPT_SETTINGS['v1'] = WRITER_PROMPT_SETTINGS['initial']
