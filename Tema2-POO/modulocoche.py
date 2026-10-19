# Módulo para ser usado por el cuaderno 12_AtributosEspeciales.ipynb
class Coche:
    def __init__(self, marca, modelo):
        self.marca = marca
        self.modelo = modelo

    def ver_coche(self):
        return f"Coche: {self.marca} {self.modelo}"