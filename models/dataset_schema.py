"""
Data models for energy community dataset schema.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class MemberData(BaseModel):
    """Data for a single energy community member."""
    member_id: str
    timestamp: datetime
    consumption: float = Field(..., alias="C_i^t", description="Load/consumption in kWh")
    generation: float = Field(..., alias="G_i^t", description="Generation in kWh")
    
    class Config:
        populate_by_name = True


class CommunityData(BaseModel):
    """Aggregated community-level data."""
    timestamp: datetime
    total_consumption: float = Field(..., alias="C_ec^t", description="Community consumption in kWh")
    total_generation: float = Field(..., alias="G_ec^t", description="Community generation in kWh")
    
    class Config:
        populate_by_name = True


class Tariff(BaseModel):
    """Energy tariff information."""
    timestamp: datetime
    time_of_use: float = Field(..., alias="ToU^t", description="Grid purchase price (€/kWh)")
    feed_in_tariff: float = Field(..., alias="FiT^t", description="Grid sale price (€/kWh)")
    internal_tariff: Optional[float] = Field(None, alias="P^t", description="Internal trading price (€/kWh)")
    
    class Config:
        populate_by_name = True


class DatasetMetadata(BaseModel):
    """Metadata describing the energy community dataset."""
    n_members: int = Field(..., description="Total number of members in the community")
    member_ids: List[str] = Field(..., description="List of member identifiers")
    time_resolution: str = Field(..., description="Time resolution (e.g., '15min', '1h')")
    start_date: datetime
    end_date: datetime
    has_community_assets: bool = Field(default=False, description="Whether EC has shared PV, BESS, EV")
    has_internal_tariff: bool = Field(default=False, description="Whether internal pricing is used")
    currency: str = Field(default="EUR")
    energy_unit: str = Field(default="kWh")
    
    # Available data columns
    available_columns: List[str] = Field(..., description="List of column names in dataset")
    
    # Column mappings
    column_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from standard names to actual column names"
    )


class ECDataset(BaseModel):
    """Complete energy community dataset."""
    metadata: DatasetMetadata
    member_data: List[MemberData] = Field(default_factory=list)
    community_data: Optional[List[CommunityData]] = None
    tariffs: List[Tariff] = Field(default_factory=list)
    
    def get_member_data(self, member_id: str) -> List[MemberData]:
        """Get all data for a specific member."""
        return [d for d in self.member_data if d.member_id == member_id]
    
    def get_timerange_data(self, start: datetime, end: datetime) -> List[MemberData]:
        """Get data within a specific time range."""
        return [d for d in self.member_data if start <= d.timestamp <= end]
