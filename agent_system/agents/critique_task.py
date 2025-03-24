from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable, Any

@dataclass
class CritiqueTask:
    """Represents a single critique task with its configuration"""
    name: str
    template: str
    needs_retrieval: bool = True
    retrieval_query: Optional[str] = None
    specialized_instructions: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    reference_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_context_from_dependencies(self, previous_results: Dict[str, str]) -> str:
        """Generate context from dependencies"""
        context = []
        for dep in self.dependencies:
            if dep in previous_results and previous_results[dep] != "None":
                context.append(f"Previous {dep.upper()} critique suggested: {previous_results[dep]}")
        return "\n".join(context)
