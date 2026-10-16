# Shared Localization Strategy Contract


class LocalizationStrategy(ABC):
    @abstractmethod
    def localize(self, issue, repository):
        pass