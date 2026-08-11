from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any


class CreativeExecutionAdapter(ABC):
    """Provider-neutral contract. Sprint 029 intentionally supplies no implementation."""

    provider: str
    capability_type: str

    @abstractmethod
    def execute(self, input_snapshot: dict[str, Any]) -> str:
        """Return a future provider output reference."""

    @abstractmethod
    def validate_output(self, output_reference: str) -> bool:
        """Validate a future provider output without registering or publishing it."""

    @abstractmethod
    def estimate_cost(self, generation_parameters: dict[str, Any]) -> Decimal:
        """Return a provider estimate; Finance remains monetary source of truth."""
