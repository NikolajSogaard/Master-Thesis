import json
from typing import Dict, Optional, Callable
from rag_retrieval import retrieve_and_generate

class Writer:
    def __init__(
            self,
            model,
            role: dict[str, str],
            structure: str,
            task: str,
            task_revision: str,
            writer_type: str = "initial",  # New parameter to identify writer type
            retrieval_fn: Optional[Callable] = None,
            ):
        self.model = model
        self.role = role
        self.structure = structure
        self.task = task
        self.task_revision = task_revision
        self.writer_type = writer_type
        self.retrieval_fn = retrieval_fn or retrieve_and_generate
        
        # Define specialized instructions for different writing tasks
        self.specialized_instructions = {
            "initial": "Focus on creating an optimal program structure based on the user's training experience, goals, and available time. Consider appropriate exercise selection, volume, intensity, and frequency.",
            "revision": "Focus on implementing feedback from the critic while maintaining program coherence. Ensure each change makes the program more effective and better suited to the user's goals.",
            "progression": "Focus on appropriate progressive overload strategies. Analyze previous performance data to guide weight selections, rep ranges, and RPE targets. Consider adaptation rate based on training history."
        }
    
    def get_retrieval_query(self, program: dict[str, str | None]) -> str:
        """Generate appropriate retrieval query based on writer type and user input"""
        user_input = program.get('user-input', '')
        
        if self.writer_type == "initial":
            return f"Best practices for designing a strength training program for {user_input}"
        elif self.writer_type == "revision":
            return "How to effectively implement feedback into a training program design?"
        elif self.writer_type == "progression":
            return "Evidence-based principles for progressive overload and week-to-week program progression in strength training"
        
        # Default fallback query
        return "Best practices for strength training program design"

    def write(
            self,
            program: dict[str, str | None],
            ) -> tuple[str, dict[str, str]]:
        # Get retrieval context first
        query = self.get_retrieval_query(program)
        retrieval_instructions = self.specialized_instructions.get(self.writer_type, "")
        
        print(f"\n--- Writer ({self.writer_type}) retrieving context ---")
        retrieval_result, _ = self.retrieval_fn(query, retrieval_instructions)
        context = f"\nRelevant context from training literature:\n{retrieval_result}\n"
        
        # Add context to the task content
        enhanced_task = self.task + context
        
        prompt = [
            self.role,
            {
                'role': 'user',
                'content': enhanced_task.format(
                    program['user-input'],
                    self.structure,
                ),
            },
        ]
        # Convert prompt to a single string as expected by the Gemini API
        combined_prompt = "\n".join(item.get("content", "") if isinstance(item, dict) else str(item) for item in prompt)
        
        print(f"Generating initial program...")
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
            override_type: str = None,  # Add parameter to override writer_type
            ) -> tuple[str, dict[str, str]]:
        # Use override_type if provided, otherwise fall back to self.writer_type
        current_type = override_type or self.writer_type
        
        # Get retrieval context
        query = "How to effectively implement critic feedback in strength training program design"
        if current_type == "progression":
            query = "How to apply progressive overload based on previous performance data in strength training"
        
        retrieval_instructions = self.specialized_instructions.get(current_type, "")
        
        print(f"\n--- Writer ({current_type}) retrieving revision context ---")
        retrieval_result, _ = self.retrieval_fn(query, retrieval_instructions)
        context = f"\nRelevant context from training literature:\n{retrieval_result}\n"
        
        # Add context to the task content
        enhanced_task_revision = self.task_revision + context
        
        prompt = [
            self.role,
            {
                'role': 'user',
                'content': enhanced_task_revision.format(
                    program['draft'],
                    program['feedback'],
                    self.structure,
                ),
            },
        ]
        # Convert prompt to a single string as expected by the Gemini API
        combined_prompt = "\n".join(item.get("content", "") if isinstance(item, dict) else str(item) for item in prompt)
        
        print(f"Revising program based on feedback...")
        # Real LLM call for revision
        draft = self.model(combined_prompt)
        
        # Handle case where draft is string (non-JSON response)
        if isinstance(draft, str):
            print(f"String response detected, wrapping in JSON structure")
            draft = {"weekly_program": {"Day 1": []}, "message": draft}
        
        return draft

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        # Check if the writer_type is "progression" (for Week 2+)
        if self.writer_type == "progression" and 'feedback' in program:
            # For progression, always use the revise method with progression task
            writer_type_for_this_call = "progression"
            print(f"Using progression writer task for Week 2+")
            # No need to temporarily update writer_type, just pass it directly
            draft = self.revise(program, override_type="progression")
            
        # For initial program creation (first iteration)
        elif 'draft' not in program or program['draft'] is None:
            writer_type_for_this_call = "initial"
            print("Initial program creation - using initial writer task")
            draft = self.write(program)
            
        # For all subsequent revisions (after first iteration)
        elif 'feedback' in program:
            writer_type_for_this_call = "revision"
            print("Program revision based on feedback - using revision task")
            # No need to temporarily update writer_type, pass the override directly
            draft = self.revise(program, override_type="revision")
            
        # Fallback (shouldn't happen in normal flow)
        else:
            writer_type_for_this_call = "initial"
            print("WARNING: Unexpected state - using initial writer task as fallback")
            draft = self.write(program)

        print(f'Current draft: {draft}')  # FIXME proper logging
        program['draft'] = draft
        return program
