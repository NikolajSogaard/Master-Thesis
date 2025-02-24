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

        # Implement the below with a real LLM call...
        # draft = self.model(prompt)
        draft = 'bad program'

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

        # Implement the below with a real LLM call...
        # draft = self.model.invoke(prompt).content
        draft = 'good program'

        return draft

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        if 'feedback' in program:
            draft = self.revise(program)
        else:
            draft = self.write(program)

        print(f'Current draft: {draft}') # FIXME proper logging

        program['draft'] = draft

        return program
