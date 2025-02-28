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
                
                # Retrieve documents for each query and combine results
                all_docs = []
                for query in queries:
                    docs = self.retriever.retrieve(query)
                    if docs:
                        all_docs.extend(docs)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_docs = [doc for doc in all_docs if not (doc in seen or seen.add(doc))]
                
                if unique_docs:
                    context = "\n\nRelevant information for training program design:\n"
                    for i, doc in enumerate(unique_docs[:5]):  # Limit to top 5 to avoid overloading
                        context += f"\n--- Document {i+1} ---\n{doc}\n"
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
            print("Retrieved relevant context for program design.")
        
        # Add specific instruction about muscle group frequency
        frequency_instruction = "\n\nIMPORTANT: Ensure each major muscle group (chest, back, legs) is trained at least TWICE per week for optimal results."
        augmented_input += frequency_instruction
        
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
