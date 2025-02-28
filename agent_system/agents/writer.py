class Writer:
    def __init__(
            self,
            model,
            role: dict[str, str],
            structure: str,
            task: str,
            task_revision: str,
            retriever=None,
            ):
        self.model = model
        self.role = role
        self.structure = structure
        self.task = task
        self.task_revision = task_revision
        self.retriever = retriever

    def _get_relevant_context(self, user_input):
        """Retrieve relevant information using RAG if available"""
        if self.retriever:
            try:
                relevant_docs = self.retriever.retrieve(user_input)
                if relevant_docs:
                    context = "\n\nRelevant information:\n" + "\n".join(relevant_docs)
                    return context
            except Exception as e:
                print(f"RAG retrieval error: {e}")
        return ""

    def write(
            self,
            program: dict[str, str | None],
            ) -> str:
        # Get relevant context if retriever is available
        context = self._get_relevant_context(program['user-input'])
        
        # Add context to the user input if available
        augmented_input = program['user-input']
        if context:
            augmented_input += context
        
        prompt = [
            self.role,
            {
                'role': 'user',
                'content': self.task.format(
                    augmented_input,
                    self.structure,
                ),
            },
        ]
        # Convert prompt to a single string as expected by the Gemini API
        combined_prompt = "\n".join(item.get("content", "") if isinstance(item, dict) else str(item) for item in prompt)
        # Real LLM call
        draft = self.model(combined_prompt)
        return draft

    def revise(
            self,
            program: dict[str, str | None],
            ) -> str:
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
        return draft

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        if 'feedback' in program and program['feedback']:
            draft = self.revise(program)
        else:
            draft = self.write(program)

        print(f'Current draft: {draft[:100]}...') # FIXME proper logging, but truncate for readability

        program['draft'] = draft

        return program
