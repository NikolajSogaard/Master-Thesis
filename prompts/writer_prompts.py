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
Create the best strength training program based on the user input below:
{}

IMPORTANT: Your output MUST be valid JSON and nothing else. Do not include any explanatory text, markdown formatting, or code block markers.
Create the program strictly in the following JSON format, as it will be directly inserted into an HTML template:
{}
'''

TASK_REVISION = '''
Revise the program below:
{}

Based on feedback from your colleague below:
{}

IMPORTANT: Your output MUST be valid JSON and nothing else. Do not include any explanatory text, markdown formatting, or code block markers.
Make sure the revised program strictly follows this JSON format, as it will be directly inserted into an HTML template:
{}
'''

PROGRAM_STRUCTURE = '''
{
  "weekly_program": {
    "Day 1": [
      {
        "name": "Exercise name",
        "sets": 3,
        "reps": "8-12",
        "target_rpe": 7,
        "rest": "60-90 seconds",
        "cues": "Brief note from AI about form, focus, or exercise purpose (keep it short)"
      }
    ],
    "Day 2": [
      {
        "name": "Exercise name",
        "sets": 4,
        "reps": "5-8",
        "target_rpe": 8,
        "rest": "2-3 minutes",
        "cues": "Brief note from AI about form, focus points, or exercise purpose (keep it short)"
      }
    ]
  }
}
'''

WRITER_PROMPT_SETTINGS: dict[str, WriterPromptSettings] = {}
WRITER_PROMPT_SETTINGS['v1'] = WriterPromptSettings(
    role={
        'role': 'system',
        'content': 'You are an AI system specialized in creating personalized strength training programs. You have expertise in exercise science, biomechanics, and training periodization. Your task is to create effective, safe, and evidence-based strength training programs tailored to the user\'s needs, goals, experience level, and available equipment. Always prioritize proper progression, injury prevention, and training variety. Provide clear, actionable instructions that are appropriate for the specified experience level.'
    },
    task=TASK,
    task_revision=TASK_REVISION,
    structure=PROGRAM_STRUCTURE,
)
# Maybe you make a second version w/ different task, etc.
