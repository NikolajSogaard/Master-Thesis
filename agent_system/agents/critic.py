class Critic:
    def __init__(
            self,
            model,
            role: dict[str, str],
            task: str,
            retriever=None,  # Add retriever parameter with default value
            ):
        self.model = model
        self.role = role
        self.task = task
        self.retriever = retriever  # Store the retriever for use in critique

    def critique(
            self,
            program: dict[str, str | None],
            ) -> dict[str, str | None]:
        # Get relevant context using retriever if available
        context = ""
        if self.retriever:
            try:
                # Query for relevant information based on the draft and user requirements
                query = f"Training program evaluation: {program['user-input'][:200]}"
                relevant_info = self.retriever.query_with_context(query)
                if relevant_info:
                    context = f"\n\nConsider this information when evaluating the program:\n{relevant_info}"
            except Exception as e:
                print(f"Error retrieving context in critic: {e}")
        
        prompt = [
            self.role,
            {
                'role': 'user',
                'content': self.task.format(
                    program['draft'],
                    program['user-input'],
                ) + context  # Add the retrieved context
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
