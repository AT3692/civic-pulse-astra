class ServiceError(Exception):
    def __init__(self, status: int, detail: str, headers: dict[str, str] | None = None):
        self.status, self.detail, self.headers = status, detail, headers or {}
        super().__init__(detail)
