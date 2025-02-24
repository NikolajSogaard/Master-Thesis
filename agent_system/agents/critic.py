class Critic:
    def __init__(
            self,
            model,
            role: dict[str, str],
            task: str,
            ):
        self.model = model

        self.role = role
        self.task = task

    def critique(
            self,
            program: dict[str, str | None],
            ) -> dict[str, str | None]:
        prompt = [
            self.role,
            {
                'role': 'user',
                'content': self.task.format(
                    program['draft'],
                    program['user-input'],
                )
            },
        ]

        # Implement the below with a real LLM call...
        # feedback = self.model(prompt)
        feedback = 'revise it!!' if program['draft'] == 'bad program' else 'None'

        if len(feedback) < 10 and 'none' in feedback.lower(): # just some sliiightly more flexible catching
            print('CrititAgent has no feedback') # FIXME proper logging
            return {'feedback': None}

        print(f'CritiAgent has feedback {feedback}') # FIXME proper logging
        return {'feedback': feedback}

    def __call__(self, article: dict[str, str | None]) -> dict[str, str | None]:
        article.update(self.critique(article))

        return article
