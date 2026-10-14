from Carrera import Carrera
from Coche import Coche


def main() -> None:
    carrera = Carrera("Gran Premio", distancia_meta=1000)
    carrera.agregar_coche(Coche("coche1", 200, 100))
    carrera.agregar_coche(Coche("coche2", 220, 100))
    carrera.agregar_coche(Coche("coche3", 240, 100))
    carrera.iniciar()


if __name__ == "__main__":
    main()
