from application.localization.strategy import LocalizationStrategy


class LocalizationService:
    def __init__(self, strategy: LocalizationStrategy):
        self.strategy = strategy

    def localize(self, issue):
        pass