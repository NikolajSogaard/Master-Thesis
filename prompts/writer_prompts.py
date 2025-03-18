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


# Ultimately, you'll likely want to extract the text fields outside of Python, but maybe easy to start this way
# You could also implement .save and .load methods as indicated above and use those 
TASK = '''
Create the best strength training program with a fitting frequency, training split, and numbers of training days, based on this input and some exercises from the user:
{}

Follow this JSON structure as a guide for your response. The Editor will handle any formatting issues:
{}

Important: 
- Make sure your program matches the persona's experience level, goals, available training time, and any specific information they've provided. Create a personalized program that directly addresses their needs.
- Make sure your program provide sufficient frequency for each major muscle group? (Each major muscle group should typically be trained at least twice per week for optimal hypertrophy)
'''

TASK_REVISION = '''
Revise the program below:
{}

Based on feedback from your colleague below:
{}

IMPORTANT: 
- You MUST directly implement all the suggested changes in the program itself, not just in the suggestion field. For example, if feedback says to increase RPE from 7 to 8-9, you should change the actual target_rpe value in the exercise.

Follow this JSON structure as a guide for your response:
{}

If this is for a subsequent week of training (Week 2+), you MUST include personalized 'suggestion' fields for each exercise based on the performance data from the previous week(except week 1). Include actual weight numbers, rep ranges, and RPE targets in your suggestions.
'''

PROGRAM_STRUCTURE = '''
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
        "suggestion": "For week 2+, include specific recommendations based on previous week's performance (e.g., 'Based on your performance, try 135lb for 3x8 at RPE 8')"
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
        "suggestion": "For week 2+, include specific recommendations based on previous week's performance (e.g., 'Increase weight by 5lb to 225lb for 4x6 at RPE 7-8')"
      }
    ],
    "Day X": etc. continue generating each training day of the week.
  }
}
'''

WRITER_PROMPT_SETTINGS: dict[str, WriterPromptSettings] = {}
WRITER_PROMPT_SETTINGS['v1'] = WriterPromptSettings(
    role={
        'role': 'system',
        'content':'You are an AI system specialized in creating personalized strength training programs.' 
                  'You have expertise in exercise science, biomechanics, and training periodization. '
                  'Your task is to create effective, and evidence-based strength training programs tailored to the user\'s needs, goals, and experience level. '
                  'Always prioritize proper progression, and training variety. '
                  'Provide clear CONCISE, actionable instructions that are appropriate for the specified experience level.'
    },
    task=TASK,
    task_revision=TASK_REVISION,
    structure=PROGRAM_STRUCTURE,
)
# Maybe you make a second version w/ different task, etc.
