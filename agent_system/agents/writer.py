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
                # Extract persona information if present
                persona_info = ""
                if "Target Persona:" in user_input:
                    persona_info = user_input.split("Target Persona:")[1].strip()
                
                # Create search queries focused on both the user input and specific training aspects
                queries = [
                    user_input,  # Original query
                    f"training program for {persona_info}" if persona_info else "",
                    "frequency training major muscle groups at least twice weekly",
                    "exercise selection for balanced muscle development",
                    "progressive overload techniques for strength training",
                ]
                
                # Filter out empty queries
                queries = [q for q in queries if q]
                
                # Combine results from different queries into one comprehensive context
                all_contexts = []
                for query in queries:
                    context = self.retriever.query_with_context(query)
                    if context and context != "No relevant information found.":
                        all_contexts.append(f"QUERY: {query}\n{context}")
                
                if all_contexts:
                    combined_context = "\n\n" + "\n\n---\n\n".join(all_contexts[:2])  # Limit to top 2 most relevant query results
                    return combined_context
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
            augmented_input += "\n\nRELEVANT TRAINING KNOWLEDGE TO INCORPORATE:\n" + context
            print("Retrieved and structured relevant context for program design.")
        
        # Add specific instruction about muscle group frequency
        frequency_instruction = "\n\nIMPORTANT: Ensure each major muscle group (chest, back, legs) is trained at least TWICE per week for optimal results."
        augmented_input += frequency_instruction
        
        # Add instruction to incorporate the retrieved knowledge
        if context:
            augmented_input += "\n\nUse the structured training knowledge provided above to create an evidence-based program."
        
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
