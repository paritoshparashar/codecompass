# Shared Localization Strategy Contract
from abc import ABC, abstractmethod


class LocalizationStrategy(ABC):
    @abstractmethod
    def localize(self, issue, repository):
        pass