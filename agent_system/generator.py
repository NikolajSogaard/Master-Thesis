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
            max_iterations: int = 3,
            ):
        # Agents
        self.writer = writer
        self.critic = critic
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
            # Remove the unsupported parameter
        )

        # Set start and end node
        graph.set_entry_point('writer')
        graph.set_finish_point('editor')

        self.app = graph.compile()

    def provide_critique(self, program: dict[str, str | None]) -> str:
        # Check if this is the first critique cycle
        if 'iteration_count' not in program:
            program['iteration_count'] = 0
            
        # Increment iteration count
        program['iteration_count'] += 1
        
        # Check if we've reached the maximum number of iterations
        if program['iteration_count'] >= self.max_iterations:
            print(f"Reached maximum iterations ({self.max_iterations}), accepting program as is.")
            return 'accept'
            
        # Check if there's feedback to consider
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
            'iteration_count': 0,  # Initialize iteration counter
        }

        final_state = self.app.invoke(program)

        return final_state
