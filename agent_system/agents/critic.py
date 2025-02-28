class Critic:
    def __init__(
            self,
            model,
            role: dict[str, str],
            task: str,
            retriever=None,
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
                # Create targeted queries for evaluation criteria
                evaluation_queries = [
                    "muscle group training frequency twice weekly evidence",
                    "optimal training volume for strength and hypertrophy",
                    "exercise selection principles for balanced development",
                    f"training guidelines for {program['user-input'][:100]}"
                ]
                
                all_contexts = []
                for query in evaluation_queries:
                    relevant_info = self.retriever.query_with_context(query)
                    if relevant_info and "No relevant information found" not in relevant_info:
                        all_contexts.append(f"EVIDENCE FOR {query.upper()}:\n{relevant_info}")
                
                if all_contexts:
                    context = "\n\nUSE THIS EVIDENCE-BASED INFORMATION TO EVALUATE THE PROGRAM:\n"
                    context += "\n\n".join(all_contexts[:2])  # Limit to top 2 most useful contexts
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
