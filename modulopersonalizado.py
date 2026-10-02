VELOCIDAD_MAX = 120


def sumar(a,b):
    return a + b


def restar(a,b):
    return a - b


class Coche:
    def __init__(self, marca, modelo):
        self.marca = marca
        self.modelo = modelo

    def ver_coche(self):
        return f"Coche: {self.marca} {self.modelo}"


