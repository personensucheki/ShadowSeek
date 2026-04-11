from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseRevenueProvider(ABC):
    name = "base"

    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """Fetches revenue data from the provider."""
        raise NotImplementedError
