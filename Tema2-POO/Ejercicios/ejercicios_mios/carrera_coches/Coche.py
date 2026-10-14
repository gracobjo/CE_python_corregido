import random


CONSUMO = 0.00999


class Coche:
    def __init__(self, nombre: str, potencia: float, combustible: float):
        self._nombre = nombre
        self._potencia = potencia
        self._combustible = combustible
        self.tiempo = 0
        self.recorrido = 0.0

    def acelerar(self) -> None:
        if self._combustible > 0:
            acelerado = random.random() * self._potencia
            self._combustible -= acelerado * CONSUMO
            self.recorrido += acelerado
            self.tiempo += 1

    def monitorizar(self) -> None:
        print(
            f"Coche: {self._nombre} - Combustible: {self._combustible:.2f}L "
            f"- Tiempo: {self.tiempo} - Recorrido: {self.recorrido:.2f} km"
        )
