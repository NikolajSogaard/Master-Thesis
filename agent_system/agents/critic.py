from typing import Dict, Optional, Callable, List
from rag_retrieval import retrieve_and_generate, retrieve_context
from .critique_task import CritiqueTask

class Critic:
    def __init__(
            self,
            model,
            role: dict[str, str],
            tasks: Dict[str, str] = None, 
            retrieval_fn: Optional[Callable] = None,
            ):
        self.model = model
        self.role = role
        self.tasks = tasks or {}
        self.retrieval_fn = retrieval_fn or retrieve_and_generate
        
        # Default specialized instructions for different task types
        self.specialized_instructions = {
            "frequency_and_split": "Provide concise guidance tailored to the user's training goals. Focus on structuring workout frequency and splits to ensure balanced coverage of muscle groups and key movement patterns. Adapt recommendations based on the user's training experience (beginner or advanced), specialization (e.g., bodybuilding or powerlifting), and overall objectives",
            "exercise_selection": "Provide concise guidance. Retrieve information about exercise selection principles based on specific user goals, experience level, and any physical limitations. Provide the answer as a list of exercises for each goal and muscle group ",            
            "rpe": "Provide consise guidance, and do not answer outside the scope of the query. Retrieve information about appropriate RPE (Rating of Perceived Exertion) targets for different exercise types and experience levels. Include guidance on when to use absolute RPE values (like 8) versus RPE ranges (like 7-8), and how RPE should differ between compound and isolation exercises.",
            "rep_ranges": "Provide concise guidance on rep ranges for different exercises, experience levels and goals. Include information on optimal rep ranges for compound and isolation exercises, as well as how rep ranges can vary based on strength, hypertrophy, or endurance goals.",
            "progression": "Focus on clear decision-making between weight or rep increases. Provide specific guidance on when to increase weight versus when to increase reps based on RPE, performance data, and position within the target rep range. For RPE below target range, consider weight increases if the user is in the middle/upper end of the rep range, but favor rep increases if the user is at the lower end of their rep range. Always consider the prescribed rep range when deciding between weight or rep increases."
        }
        
        # Define task types based on available tasks
        if tasks and "progression" in tasks and len(tasks) == 1:
            # If only progression task is available, we're in Week 2+ mode
            self.task_types = ["progression"]
            self.is_week2plus = True
        else:
            # Default Week 1 tasks
            self.task_types = ["frequency_and_split", "exercise_selection", "set_volume", "rep_ranges", "rpe"]
            self.is_week2plus = False

        # Define task configurations
        self.task_configs = {
            "frequency_and_split": CritiqueTask(
                name="frequency_and_split",
                template=self.tasks.get("frequency_and_split", ""),
                needs_retrieval=True,
                retrieval_query="How do I structure a training plan for {user_input}? What are good training frequency and training splits for strength training programs?",
                specialized_instructions=self.specialized_instructions.get("frequency_and_split", ""),
                dependencies=[],
            ),
            "exercise_selection": CritiqueTask(
                name="exercise_selection",
                template=self.tasks.get("exercise_selection", ""),
                needs_retrieval=True,
                retrieval_query="What exercises are most effective and appropriate for different muscle groups based on: {user_input}. Give 3 exampel exercises for each movement pattern: Upper: Horizontal Push (Chest/pressing), Upper: Horizontal Pull (Rows/rear back), Upper: Vertical Push (Overhead/shoulders), Upper: Vertical Pull (Pull-ups/lats), Lower: Anterior Chain (Quads), Lower: Posterior Chain (Glutes/Hams)",
                specialized_instructions=self.specialized_instructions.get("exercise_selection", ""),
                dependencies=["frequency_and_split"],
            ),
            "set_volume": CritiqueTask(
                name="set_volume",
                template=self.tasks.get("set_volume", ""),
                needs_retrieval=False,
                dependencies=["frequency_and_split", "exercise_selection"],
                reference_data={
                    "volume_guidelines": {
                        "beginner": {
                            # Old muscle group guidelines
                            #"back": {"min": 8, "max": 10},
                            #"chest": {"min": 8, "max": 10},
                            #"hamstrings": {"min": 6, "max": 10},
                            #"quads": {"min": 8, "max": 10},
                            
                            # New movement pattern guidelines
                            "Upper_horizontal_push": {"min": 6, "max": 10, "description": "Chest/pressing"},
                            "Upper_horizontal_pull": {"min": 6, "max": 10, "description": "Rows/rear back"},
                            "Upper_vertical_push": {"min": 6, "max": 10, "description": "Overhead/shoulders"},
                            "Upper_vertical_pull": {"min": 6, "max": 10, "description": "Pull-ups/lats"},
                            "Lower_anterior_chain": {"min": 6, "max": 10, "description": "Quads"},
                            "Lower_posterior_chain": {"min": 6, "max": 10, "description": "Glutes/Hams"}
                        },
                        "intermediate": {
                            # Old muscle group guidelines
                            #"back": {"min": 10, "max": 20},
                            #"chest": {"min": 10, "max": 15},
                            #"hamstrings": {"min": 8, "max": 12},
                            #"quads": {"min": 10, "max": 15},
                            #"shoulders": {"min": 10, "max": 20},
                            #"glutes": {"min": 10, "max": 20},
                            
                            # New movement pattern guidelines
                            "Upper_horizontal_push": {"min": 10, "max": 16, "description": "Chest/pressing"},
                            "Upper_horizontal_pull": {"min": 10, "max": 16, "description": "Rows/rear back"},
                            "Upper_vertical_push": {"min": 8, "max": 14, "description": "Overhead/shoulders"},
                            "Upper_vertical_pull": {"min": 10, "max": 18, "description": "Pull-ups/lats"},
                            "Lower_anterior_chain": {"min": 10, "max": 16, "description": "Quads"},
                            "Lower_posterior_chain": {"min": 10, "max": 16, "description": "Glutes/Hams"}
                        },
                        "advanced": {
                            # New movement pattern guidelines
                            "Upper_horizontal_push": {"min": 10, "max": 16, "description": "Chest/pressing"},
                            "Upper_horizontal_pull": {"min": 10, "max": 16, "description": "Rows/rear back"},
                            "Upper_vertical_push": {"min": 8, "max": 14, "description": "Overhead/shoulders"},
                            "Upper_vertical_pull": {"min": 10, "max": 18, "description": "Pull-ups/lats"},
                            "Lower_anterior_chain": {"min": 10, "max": 16, "description": "Quads"},
                            "Lower_posterior_chain": {"min": 10, "max": 16, "description": "Glutes/Hams"}
                        }
                    }
                }
            ),
            "rep_ranges": CritiqueTask(
                name="rep_ranges",
                template=self.tasks.get("rep_ranges", ""),
                needs_retrieval=True,
                retrieval_query="What are optimal rep ranges for specific exercises and for different strength training goals?",
                specialized_instructions=self.specialized_instructions.get("rep_ranges", ""),
                dependencies=["frequency_and_split", "exercise_selection", "set_volume"],
            ),
            "rpe": CritiqueTask(
                name="rpe",
                template=self.tasks.get("rpe", ""),
                needs_retrieval=True,
                retrieval_query="How should RPE targets be assigned in strength training for different types exercises and experience levels?",
                specialized_instructions=self.specialized_instructions.get("rpe", ""),
                dependencies=["frequency_and_split", "exercise_selection", "set_volume", "rep_ranges"],
            ),
            "progression": CritiqueTask(
                name="progression",
                template=self.tasks.get("progression", ""),
                needs_retrieval=True,
                retrieval_query="What are the best practices for progressive overload, and when should weight be increased/decreasing versus reps? Come with consise guidance on how to choose between increasing/decreasing weight versus increasing reps for progressive overload. When should I prioritize rep increases/decreasing over weight increases if the user is at the lower end of their target rep range? How should RPE feedback influence whether to add weight or reps?",
                specialized_instructions=self.specialized_instructions.get("progression", ""),
                dependencies=[],
            )
        }

    def get_task_query(self, program: dict[str, str | None], task_type: str) -> str:
        """Generate an appropriate query based on task type and week."""
        
        # Week 2+ specific queries
        if self.is_week2plus and task_type == "progression":
            return "What are the best practices for progressive overload, and when should weight be increased/decreasing versus reps? Come with consise guidance on how to choose between increasing/decreasing weight versus increasing reps for progressive overload. When should I prioritize rep increases/decreasing over weight increases if the user is at the lower end of their target rep range? How should RPE feedback influence whether to add weight or reps?"
        
        # Week 1 queries 
        queries = {
            "frequency_and_split": "How do I structure a training plan for {user_input}? What are good training frequency and training splits for strength training programs?",
            "exercise_selection": "What exercises are most effective and appropriate for different muscle groups based on: {user_input}. Give 3 exampel exercises for each movement pattern: Upper: Horizontal Push (Chest/pressing), Upper: Horizontal Pull (Rows/rear back), Upper: Vertical Push (Overhead/shoulders), Upper: Vertical Pull (Pull-ups/lats), Lower: Anterior Chain (Quads), Lower: Posterior Chain (Glutes/Hams)",            
            "rep_ranges": "What are optimal rep ranges for specific exercises and for different strength training goals?",
            "rpe": "How should RPE targets be assigned in strength training for different types exercises and experience levels?",
        }
        
        return queries.get(task_type, f"Best practices for {task_type} in strength training programs")

    def run_single_critique(
            self,
            program: dict[str, str | None],
            task_type: str,
            previous_results: Dict[str, str] = None
            ) -> str:
        """Run a single critique with specialized RAG retrieval."""
        previous_results = previous_results or {}
        print(f"\n--- Running {task_type.upper()} critique ---")
        
        # Get task configuration
        task_config = self.task_configs.get(task_type)
        if not task_config:
            print(f"No configuration for {task_type}, using default...")
            # Create default configuration
            task_config = CritiqueTask(
                name=task_type,
                template=self.tasks.get(task_type, ""),
                needs_retrieval=True,
                retrieval_query=f"Best practices for {task_type} in strength training programs",
                specialized_instructions="",
                dependencies=[],
            )
        
        # Get context from dependencies
        dependency_context = task_config.get_context_from_dependencies(previous_results)
        
        # Include reference data if available for set_volume task
        reference_data_context = ""
        if task_type == "set_volume" and task_config.reference_data.get("volume_guidelines"):
            print(f"Including volume guidelines from reference data...")
            volume_data = task_config.reference_data["volume_guidelines"]
            reference_data_context = "\nVolume guidelines from reference data:\n"
            
            for level in ["beginner", "intermediate", "advanced"]:
                if level in volume_data:
                    reference_data_context += f"\n{level.capitalize()} level:\n"
                    for muscle, ranges in volume_data[level].items():
                        min_val = ranges.get("min", "?") 
                        max_val = ranges.get("max", "?")
                        reference_data_context += f"- {muscle.capitalize()}: {min_val}-{max_val} sets per week\n"
        
        # Retrieve context if needed
        if task_config.needs_retrieval:
            print(f"Retrieving context...")
            retrieval_query = task_config.retrieval_query
            if "{user_input}" in retrieval_query:
                user_input = program.get('user-input', '')
                retrieval_query = retrieval_query.format(user_input=user_input)
            retrieval_result, _ = self.retrieval_fn(
                retrieval_query, 
                task_config.specialized_instructions
            )
            context = f"\nRelevant context from training literature:\n{retrieval_result}\n"
        else:
            print(f"Skipping retrieval for {task_type} - using only task template guidance...")
            context = ""
        if reference_data_context:
            context = reference_data_context + "\n" + context
        if dependency_context:
            print(f"Including feedback from {len(task_config.dependencies)} previous critiques...")
            context = f"\nConsiderations from previous critiques:\n{dependency_context}\n{context}"
        
        # Make sure 'draft' contains the actual program content
        program_content = program.get('draft')
        if isinstance(program_content, dict) and 'weekly_program' in program_content:
            import json
            program_content = json.dumps(program_content, indent=2)
        
        # Use the specific task template for this task_type if available
        task_template = self.tasks.get(task_type)
        if task_template is None:
            # If no template is available, use a default format
            task_template = f'''
            Your colleague has written the following training program:
            {{}}
            For an individual who provided the following input:
            {{}}
            Focus specifically on the {task_type.upper()}. Provide feedback if any... otherwise only return "None"
            '''
        
        # For Week 2+ progression task, format with week number and feedback data
        if self.is_week2plus and task_type == "progression":
            week_number = program.get('week_number', 2)
            user_input = program.get('user-input', '')
            feedback_data = program.get('feedback', '{}')
            task_template = task_template.replace("{week_number}", str(week_number))
            prompt_content = task_template.format(
                program_content,
                user_input,
                feedback_data
            ) + context
        else:
            # Regular Week 1 formatting
            prompt_content = task_template.format(
                program_content,
                program.get('user-input', ''),
            ) + context
        
        # Format system instructions
        system_instructions = self.role.get('content', '')
        full_prompt = f"{system_instructions}\n\n{prompt_content}"
        
        print(f"Generating critique...")
        try:
            feedback = self.model(full_prompt)
            return feedback if feedback else None
        except Exception as e:
            print(f"Error in {task_type.upper()} critique: {e}")
            return f"Error in {task_type} critique: {str(e)}"

    def critique(self, program: dict[str, str | None]) -> dict[str, str | None]:
        """Run each critique type sequentially with its own RAG retrieval."""
        print("\n========== CRITIQUE PROCESS STARTED ==========")
        all_feedback = []
        previous_results = {}
        
        # Run each task type with its own specialized retrieval
        for task_type in self.task_types:
            feedback = self.run_single_critique(program, task_type, previous_results)
            if feedback and isinstance(feedback, str) and len(feedback.strip()) > 10:
                processed_feedback = feedback
                if feedback.strip().endswith("None"):
                    processed_feedback = feedback.strip()[:-4].strip()
                if processed_feedback and len(processed_feedback.strip()) > 10:
                    previous_results[task_type] = processed_feedback
                if processed_feedback and 'no changes' not in processed_feedback.lower() and 'therefore, no changes' not in processed_feedback.lower():
                    formatted_feedback = f"[{task_type.upper()} FEEDBACK]:\n{processed_feedback}\n" 
                    all_feedback.append(formatted_feedback)
                    print(f"\n{'='*50}")
                    print(f"{task_type.upper()} CRITIQUE:")
                    print(f"{'='*50}")
                    words = processed_feedback.split()
                    line = ""
                    for word in words:
                        if len(line) + len(word) > 80:
                            print(line)
                            line = word + " "
                        else:
                            line += word + " "
                    if line:
                        print(line)
                    print(f"{'='*50}\n")
                else:
                    print(f"\n{task_type.upper()} - Analysis performed but no changes needed")
            else:
                print(f"\n{task_type.upper()} - No significant feedback provided")
        
        if not all_feedback:
            print('No feedback from any critique tasks')
            return {'feedback': None}
        
        # Combine all feedback with section headers
        combined_feedback = "\n".join(all_feedback)
        print(f"\n========== CRITIQUE PROCESS COMPLETE ({len(all_feedback)}/{len(self.task_types)}) ==========")
        return {'feedback': combined_feedback}

    def __call__(self, article: dict[str, str | None]) -> dict[str, str | None]:
        """Make the Critic callable."""
        article.update(self.critique(article))
        return article
