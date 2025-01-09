from pydantic import BaseModel
from typing import Dict, Optional

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: int
    weight: float

class Inventory(BaseModel):
    items: Dict[str, Item] = {}

    def add_item(self, item: Item):
        if item.name in self.items:
            self.items[item.name].quantity += item.quantity
        else:
            self.items[item.name] = item

    def remove_item(self, item_name: str, quantity: int = 1):
        if item_name in self.items:
            if self.items[item_name].quantity > quantity:
                self.items[item_name].quantity -= quantity
            elif self.items[item_name].quantity == quantity:
                del self.items[item_name]
            else:
                raise ValueError(f"Not enough {item_name} to remove")
        else:
            raise ValueError(f"{item_name} not found in inventory")
