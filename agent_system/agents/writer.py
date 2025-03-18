#to doo: add relevant retrival

import json

class Writer:
    def __init__(
            self,
            model,
            role: dict[str, str],
            structure: str,
            task: str,
            task_revision: str,
            ):
        self.model = model
        self.role = role
        self.structure = structure
        self.task = task
        self.task_revision = task_revision

    def write(
            self,
            program: dict[str, str | None],
            ) -> tuple[str, dict[str, str]]:
        prompt = [
            self.role,
            {
                'role': 'user',
                'content': self.task.format(
                    program['user-input'],
                    self.structure,
                ),
            },
        ]
        # Convert prompt to a single string as expected by the Gemini API
        combined_prompt = "\n".join(item.get("content", "") if isinstance(item, dict) else str(item) for item in prompt)
        # Real LLM call
        draft = self.model(combined_prompt)
        
        # Handle case where draft is string (non-JSON response)
        if isinstance(draft, str):
            print(f"String response detected, wrapping in JSON structure")
            draft = {"weekly_program": {"Day 1": []}, "message": draft}
        
        return draft

    def revise(
            self,
            program: dict[str, str | None],
            ) -> tuple[str, dict[str, str]]:
        prompt = [
            self.role,
            {
                'role': 'user',
                'content': self.task_revision.format(
                    program['draft'],
                    program['feedback'],
                    self.structure,
                ),
            },
        ]
        # Convert prompt to a single string as expected by the Gemini API
        combined_prompt = "\n".join(item.get("content", "") if isinstance(item, dict) else str(item) for item in prompt)
        # Real LLM call for revision
        draft = self.model(combined_prompt)
        
        # Handle case where draft is string (non-JSON response)
        if isinstance(draft, str):
            print(f"String response detected, wrapping in JSON structure")
            draft = {"weekly_program": {"Day 1": []}, "message": draft}
        
        return draft

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        if 'feedback' in program:
            draft = self.revise(program)
        else:
            draft = self.write(program)

        print(f'Current draft: {draft}') # FIXME proper logging

        program['draft'] = draft

        return program
