from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Variant:
    ib: Optional[str] = None
    other_data: Dict[str, str] = field(default_factory=dict)


@dataclass
class Component:
    name: str
    shared: Dict[str, Optional[str]]
    variants: Dict[str, Variant]
