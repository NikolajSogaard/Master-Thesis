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
        
        # Ensure draft is properly formatted
        if isinstance(draft, dict) and 'weekly_program' in draft:
            return draft
        elif isinstance(draft, str):
            try:
                parsed = json.loads(draft)
                if 'weekly_program' in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
        
        # If we get here, wrap the draft in the expected structure
        return {"weekly_program": draft if isinstance(draft, dict) else {}}

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
        
        # Same formatting check as in write method
        if isinstance(draft, dict) and 'weekly_program' in draft:
            return draft
        elif isinstance(draft, str):
            try:
                parsed = json.loads(draft)
                if 'weekly_program' in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
        
        # If we get here, wrap the draft in the expected structure
        return {"weekly_program": draft if isinstance(draft, dict) else {}}

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        if 'feedback' in program:
            draft = self.revise(program)
        else:
            draft = self.write(program)

        print(f'Current draft: {draft}') # FIXME proper logging

        program['draft'] = draft

        return program
