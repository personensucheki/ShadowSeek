class BasePlugin:
    name = "base"
    description = "Base plugin"
    enabled = True

    def run(self, data: dict) -> dict:
        raise NotImplementedError

    def error_result(self, message="Plugin execution failed.") -> dict:
        return {"success": False, "error": message}
