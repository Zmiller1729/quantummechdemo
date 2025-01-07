from pydantic import BaseModel, validator
from typing import Optional, List
from .inventory import Inventory  # Import Inventory model

VALID_CLASSES = ["Warrior", "Mage", "Rogue", "Cleric"]
VALID_RACES = ["Human", "Elf", "Dwarf", "Orc"]
VALID_ALIGNMENTS = ["Lawful Good", "Neutral", "Chaotic Evil"]

class Player(BaseModel):
    name: str
    level: int
    class_type: str
    race: str
    background: Optional[str] = None
    alignment: Optional[str] = None
    experience_points: int = 0
    inventory: Inventory = Inventory()

    @validator('class_type')
    def validate_class_type(cls, value):
        if value not in VALID_CLASSES:
            raise ValueError(f'Invalid class type: {value}. Valid options are: {VALID_CLASSES}')
        return value

    @validator('race')
    def validate_race(cls, value):
        if value not in VALID_RACES:
            raise ValueError(f'Invalid race: {value}. Valid options are: {VALID_RACES}')
        return value

    @validator('alignment')
    def validate_alignment(cls, value):
        if value and value not in VALID_ALIGNMENTS:
            raise ValueError(f'Invalid alignment: {value}. Valid options are: {VALID_ALIGNMENTS}')
        return value
