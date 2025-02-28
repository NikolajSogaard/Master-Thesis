class Retriever:
    def __init__(self, knowledge_source=None):
        self.knowledge_source = knowledge_source

    def retrieve(self, query: str) -> str:
        # Basic stub method for retrieval
        return "Relevant context based on: " + query

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        context = self.retrieve(program['user-input'])
        program['retrieved_context'] = context
        return program
