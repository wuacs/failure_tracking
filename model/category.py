from enum import Enum

class DefaultCategory(Enum):
    SLIP = "slip"
    WORDING_UNCLEAR = "wording_unclear"
    NA = "n/a"

class Category():
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
