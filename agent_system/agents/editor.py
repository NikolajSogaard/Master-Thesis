class Editor:
    def __init__(self):
        pass

    def format_program(self, program: dict[str, str | None]) -> dict:
        # Now the draft is already a properly formatted dictionary,
        # so we just need to return it as-is or with minimal processing
        draft = program['draft']
        
        # If draft is already in the right format, return it directly
        if isinstance(draft, dict):
            return draft
            
        # If it's not a dict (unlikely with our fixes), return an empty structure
        return {"weekly_program": {}}

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        program['formatted'] = self.format_program(program)
        return program
