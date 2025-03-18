import json

class Editor:
    def __init__(self):
        pass

    def format_program(self, program: dict[str, str | None]) -> dict:
        """Ensure the program is in the correct format for the web application."""
        draft = program['draft']
        # Debug logging added to inspect draft content and type
        print("DEBUG: Editor received draft (type {}): {}".format(type(draft), draft))
        
        # Case 1: If draft is already a dict with 'weekly_program' key
        if isinstance(draft, dict) and 'weekly_program' in draft:
            return draft
        
        # Case 2: If draft is a dict but missing 'weekly_program' key
        if isinstance(draft, dict):
            return {"weekly_program": draft}
        
        # Case 3: If draft is a string, try to parse it as JSON
        if isinstance(draft, str):
            try:
                parsed = json.loads(draft)
                # If parsed JSON has 'weekly_program' key
                if isinstance(parsed, dict) and 'weekly_program' in parsed:
                    return parsed
                # If parsed JSON is missing 'weekly_program' key
                elif isinstance(parsed, dict):
                    return {"weekly_program": parsed}
            except json.JSONDecodeError:
                # If string is not valid JSON, wrap it in a default structure
                return {"weekly_program": {}}
        
        # Default case: Return empty structure for any other type
        return {"weekly_program": {}}

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        formatted = self.format_program(program)
        # Preserve Critic feedback if available
        if 'feedback' in program:
            formatted['critic_feedback'] = program['feedback']
        program['formatted'] = formatted
        return program
