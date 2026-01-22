"""
Data models for structured paper specifications.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ModelType(str, Enum):
    """Type of energy sharing model."""
    SELF_CONSUMPTION = "self_consumption"
    BILL_POOLING = "bill_pooling"
    VIRTUAL_NET_METERING = "virtual_net_metering"
    P2P_TRADING = "p2p_trading"
    COST_ALLOCATION = "cost_allocation"
    BENEFIT_SHARING = "benefit_sharing"
    HYBRID = "hybrid"
    OTHER = "other"


class Variable(BaseModel):
    """A variable used in the model."""
    name: str = Field(..., description="Variable name (e.g., 'C_i^t')")
    description: str = Field(..., description="What the variable represents")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    type: str = Field(..., description="Data type: continuous, discrete, binary")
    is_decision_var: bool = Field(default=False, description="Whether it's a decision variable")
    is_parameter: bool = Field(default=False, description="Whether it's a parameter")


class Equation(BaseModel):
    """Mathematical equation or formula."""
    name: str = Field(..., description="Equation identifier")
    latex: str = Field(..., description="LaTeX representation")
    description: str = Field(..., description="Plain English description")
    variables_used: List[str] = Field(default_factory=list)


class Algorithm(BaseModel):
    """Algorithm steps."""
    name: str
    description: str
    steps: List[str] = Field(..., description="Ordered list of algorithm steps")
    complexity: Optional[str] = None


class PaperSpec(BaseModel):
    """Structured specification extracted from a research paper."""

    model_config = ConfigDict(extra="ignore")
    
    # Metadata
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    
    # Model information
    model_type: ModelType
    model_name: str = Field(..., description="Name of the specific model/method")
    
    # Description
    objective: str = Field(..., description="What the model aims to achieve")
    summary: Optional[str] = Field(None, description="High-level summary of the approach")
    
    # Mathematical formulation
    variables: List[Variable] = Field(default_factory=list)
    equations: List[Equation] = Field(default_factory=list)

    algorithm: Optional[Algorithm] = None
    pseudocode: Optional[str] = Field(None, description="Pseudocode for the model")
