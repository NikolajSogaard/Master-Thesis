class Editor:
    def __init__(self):
        pass

    def format_program(self, program: dict[str, str | None]) -> str:
        # Could contain some logic to transform JSON repr to nicer format
        return program['draft'].title()

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        program['formatted'] = self.format_program(program)

        return program
