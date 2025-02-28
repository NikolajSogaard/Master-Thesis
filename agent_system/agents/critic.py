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

        # Convert prompt to a single string as expected by the Gemini API
        combined_prompt = "\n".join(item.get("content", "") if isinstance(item, dict) else str(item) for item in prompt)
        
        # Real LLM call
        feedback = self.model(combined_prompt)

        if len(feedback) < 10 and 'none' in feedback.lower(): # just some sliiightly more flexible catching
            print('CriticAgent has no feedback') # FIXME proper logging
            return {'feedback': None}

        print(f'CriticAgent has feedback: {feedback[:100]}...') # FIXME proper logging, truncated for readability
        return {'feedback': feedback}

    def __call__(self, article: dict[str, str | None]) -> dict[str, str | None]:
        article.update(self.critique(article))
        return article
