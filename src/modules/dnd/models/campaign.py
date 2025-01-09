from pydantic import BaseModel
from typing import List, Optional
from .npc import NPC  # Import NPC model

class Location(BaseModel):
    name: str
    description: Optional[str] = None
    npcs: List[NPC]

class Area(BaseModel):
    name: str
    description: Optional[str] = None
    locations: List[Location]

class Chapter(BaseModel):
    title: str
    summary: Optional[str] = None
    areas: List[Area]

class Act(BaseModel):
    title: str
    chapters: List[Chapter]

class Campaign(BaseModel):
    title: str
    description: Optional[str] = None
    acts: List[Act]
    areas: List[Area]
