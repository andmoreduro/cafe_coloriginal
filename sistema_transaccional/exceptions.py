class SesionInvalida(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)


class SesionNoCacheada(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)