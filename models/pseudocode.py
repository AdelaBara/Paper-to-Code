"""
Data models for pseudocode representation.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum


class StatementType(str, Enum):
    """Type of pseudocode statement."""
    ASSIGNMENT = "assignment"
    CONDITION = "condition"
    LOOP = "loop"
    FUNCTION_CALL = "function_call"
    RETURN = "return"
    COMMENT = "comment"


class PseudocodeStatement(BaseModel):
    """A single pseudocode statement."""
    line_number: int
    type: StatementType
    content: str = Field(..., description="The pseudocode line")
    indentation_level: int = Field(default=0)
    comment: Optional[str] = None


class PseudocodeFunction(BaseModel):
    """A function in pseudocode."""
    name: str
    description: str
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    statements: List[PseudocodeStatement] = Field(default_factory=list)


class AdaptedLogic(BaseModel):
    """Adapted logic after mapping to user dataset."""
    original_spec_ref: str = Field(..., description="Reference to original paper spec")
    
    # Variable mappings
    variable_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Map from paper variables to dataset columns"
    )
    
    # Adapted components
    adapted_summary: str
    dataset_compatibility_notes: List[str] = Field(default_factory=list)
    missing_data_workarounds: List[str] = Field(default_factory=list)
    
    # Additional computations needed
    derived_variables: List[str] = Field(
        default_factory=list,
        description="Variables that need to be computed from available data"
    )


class Pseudocode(BaseModel):
    """Complete pseudocode representation."""
    
    # Metadata
    model_name: str
    version: str = Field(default="1.0")
    adapted_from: Optional[str] = None
    
    # Structure
    global_variables: List[str] = Field(default_factory=list)
    constants: Dict[str, str] = Field(default_factory=dict)
    
    functions: List[PseudocodeFunction] = Field(default_factory=list)
    main_algorithm: PseudocodeFunction
    
    # Adaptation info
    adapted_logic: Optional[AdaptedLogic] = None
    
    # Human review
    review_status: str = Field(default="pending")  # pending, approved, needs_revision
    review_comments: List[str] = Field(default_factory=list)
    revisions: List[str] = Field(default_factory=list)
    
    def to_markdown(self) -> str:
        """Convert pseudocode to markdown format."""
        lines = [f"# {self.model_name} - Pseudocode\n"]
        
        if self.constants:
            lines.append("## Constants")
            for name, value in self.constants.items():
                lines.append(f"- `{name}` = {value}")
            lines.append("")
        
        if self.global_variables:
            lines.append("## Global Variables")
            for var in self.global_variables:
                lines.append(f"- `{var}`")
            lines.append("")
        
        for func in self.functions:
            lines.append(f"## Function: {func.name}")
            lines.append(f"**Description**: {func.description}")
            lines.append(f"**Inputs**: {', '.join(func.inputs)}")
            lines.append(f"**Outputs**: {', '.join(func.outputs)}")
            lines.append("\n```")
            for stmt in func.statements:
                indent = "  " * stmt.indentation_level
                lines.append(f"{indent}{stmt.content}")
            lines.append("```\n")
        
        lines.append("## Main Algorithm")
        lines.append("```")
        for stmt in self.main_algorithm.statements:
            indent = "  " * stmt.indentation_level
            lines.append(f"{indent}{stmt.content}")
        lines.append("```")
        
        return "\n".join(lines)
