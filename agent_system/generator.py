from langgraph.graph import Graph

from .agents import (
    Writer,
    Critic,
    Editor,
)

class ProgramGenerator:
    def __init__(
            self,
            writer: Writer,
            critic: Critic,
            editor: Editor,
            max_iterations: int = 3, #default maximum iterations for critique and revision
            ):
        # Agents
        self.writer = writer
        self.critic = critic
        
        # Pass writer to editor to enable implementing final feedback
        if not hasattr(editor, 'writer') or editor.writer is None:
            editor.writer = writer
            
        self.editor = editor
        self.max_iterations = max_iterations

        # Build graph
        graph = Graph()

        # Agent nodes
        graph.add_node('writer', self.writer)
        graph.add_node('critic', self.critic)
        graph.add_node('editor', self.editor)

        # Arcs
        graph.add_edge(
            start_key='writer',
            end_key='critic',
        )
        graph.add_conditional_edges(
            source='critic',
            path=self.provide_critique,
            path_map={
                'accept': 'editor',
                'revise': 'writer',
            },
        )

        # Set start and end node
        graph.set_entry_point('writer')
        graph.set_finish_point('editor')
        self.app = graph.compile()

    def provide_critique(self, program: dict[str, str | None]) -> str:
        if 'iteration_count' not in program:
            program['iteration_count'] = 0
        program['iteration_count'] += 1
        if program['iteration_count'] >= self.max_iterations:
            print(f"Reached maximum iterations ({self.max_iterations}), accepting program as is.")
            return 'accept'
        if program['feedback'] is None:
            return 'accept'
        return 'revise'

    def create_program(
            self,
            user_input: str,
            ) -> dict[str, str | None]:
        # Prepare inputs
        program = {
            'user-input': user_input,
            'draft': None,  
            'feedback': None,
            'formatted': None,
            'iteration_count': 0,
        }

        final_state = self.app.invoke(program)

        return final_state
