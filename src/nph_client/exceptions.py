class NPHClientError(Exception):
    """Exceção base para erros da biblioteca nph-client."""


class NPHAuthError(NPHClientError):
    """Lançada quando a apiKey está ausente, inválida ou sem permissão."""


class NPHAPIError(NPHClientError):
    """Lançada quando ocorre erro HTTP ou de comunicação com a API do NPH."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code