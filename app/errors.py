class ReglaNegocioError(Exception):
    """Se violó una regla del negocio (la API responde con el #409 y ya.)."""
