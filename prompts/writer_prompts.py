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
Create the best program based on the user input below:
{}
Create the program in the following format, making sure to only return valid JSON:
{}
''' # Create training program, etc.
TASK_REVISION = '''
Revise the program below:
{}
Based on feedback from your colleague below:
{}
Make sure the revised progam follows the format below, making sure to only return valid JSON:
{}
'''

PROGRAM_STRUCTURE = '''
{
  "program_name": "Name of the strength training program",
  "duration_weeks": 8,
  "sessions_per_week": 3,
  "target_goals": ["strength", "hypertrophy", "endurance"],
  "difficulty_level": "beginner/intermediate/advanced",
  "notes": "Any general notes about the program",
  "workouts": [
    {
      "day": 1,
      "name": "Upper Body",
      "exercises": [
        {
          "name": "Exercise name",
          "sets": 3,
          "reps": "8-12",
          "rest_seconds": 60,
          "notes": "Optional form cues or tips"
        }
      ]
    }
  ],
  "progression_plan": "Description of how to progress over time"
}
''' # Structure output this way, e.g., some JSON format


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
