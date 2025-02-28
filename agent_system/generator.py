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
            max_iterations=3,
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
        )

        # Set start and end node
        graph.set_entry_point('writer')
        graph.set_finish_point('editor')

        self.app = graph.compile()

    def provide_critique(self, program: dict[str, str | None]) -> str:
        if program['feedback'] is None:
            return 'accept'

        return 'revise'

    def create_program(
            self,
            user_input: str,
            ) -> dict[str, str | None]:
        """
        Create a training program based on user input.
        
        Args:
            user_input: User's requirements for the program
            
        Returns:
            Dictionary containing the final program and related information
        """
        # Initialize the program dictionary
        program = {
            'user-input': user_input,
            'draft': None,
            'feedback': None,
            'formatted': None,
            'iterations': 0,
        }
        
        # Generate initial draft
        program = self.writer(program)
        
        # Iterate until no more feedback or max iterations reached
        for i in range(self.max_iterations):
            program['iterations'] = i + 1
            
            # Get feedback from critic
            program = self.critic(program)
            
            # If no feedback, break the loop
            if not program.get('feedback'):
                break
                
            # Revise based on feedback
            program = self.writer(program)
        
        # Format the final program
        program = self.editor(program)
        
        return program
