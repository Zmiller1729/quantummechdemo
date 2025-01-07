from pydantic import BaseModel
from typing import List, Optional

class NPC(BaseModel):
    name: str
    role: str
    description: Optional[str] = None
