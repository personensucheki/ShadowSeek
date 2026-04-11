class BaseProvider:
    """
    Basis-Provider für Creator-Metriken. Implementiert Interface für weitere Plattformen.
    """
    def search_creator(self, username, platform, realname=None, deepsearch=False):
        raise NotImplementedError("Provider muss search_creator implementieren.")
