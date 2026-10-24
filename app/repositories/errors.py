class RepositorioError(Exception):
    """Error base de persistencia."""


class RegistroNoEncontrado(RepositorioError):
    pass


class DatosCorruptos(RepositorioError):
    """El CSV no coincide con el modelo (encabezados o valores inválidos)."""