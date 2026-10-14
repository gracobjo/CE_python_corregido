from __future__ import annotations

from typing import List, Protocol


class CocheParticipante(Protocol):
    _nombre: str
    _combustible: float
    recorrido: float
    tiempo: int

    def acelerar(self) -> None: ...

    def monitorizar(self) -> None: ...

class Carrera:
    """
    Clase que gestiona una carrera de coches.
    La carrera finaliza cuando algún coche ha recorrido la distancia completa.
    """
    
    def __init__(self, nombre: str, distancia_meta: float = 1000):
        """
        Inicializa una nueva carrera.
        
        Args:
            nombre: Nombre de la carrera
            distancia_meta: Distancia total a recorrer (por defecto 1000)
        """
        self._nombre = nombre
        self._distancia_meta = distancia_meta
        self._coches: List[CocheParticipante] = []
        self._combustible_inicial: List[float] = []
        self._tiempo_carrera = 0
        self._finalizada = False
        self._ganador = None
    
    def agregar_coche(self, coche: CocheParticipante) -> None:
        """
        Añade un coche a la carrera.
        
        Args:
            coche: Instancia de Coche a participar
        """
        self._coches.append(coche)
        self._combustible_inicial.append(coche._combustible)
        print(f"✅ {coche._nombre} se une a la carrera")
    
    def hay_ganador(self) -> bool:
        """
        Verifica si hay algún coche que haya completado la carrera.
        Usa all() para comprobar si TODOS los coches NO han terminado aún.
        
        Returns:
            True si algún coche ha llegado a la meta, False en caso contrario
        """
        return any(coche.recorrido >= self._distancia_meta for coche in self._coches)
    
    def determinar_ganador(self) -> CocheParticipante:
        """
        Determina el coche ganador (el que más ha recorrido).
        
        Returns:
            El coche que más distancia ha recorrido
        """
        return max(self._coches, key=lambda c: c.recorrido)
    
    def mostrar_clasificacion(self) -> None:
        """Muestra la clasificación actual de la carrera ordenada por distancia."""
        clasificacion = sorted(self._coches, key=lambda c: c.recorrido, reverse=True)
        
        print(f"\n{'='*70}")
        print(f"📊 CLASIFICACIÓN - {self._nombre}")
        print(f"{'='*70}")
        for posicion, coche in enumerate(clasificacion, 1):
            print(f"{posicion}. {coche._nombre}: {coche.recorrido:.2f} km "
                  f"(Combustible: {coche._combustible:.2f}L)")
        print(f"{'='*70}\n")
    
    def simular_vuelta(self) -> None:
        """Simula una vuelta/iteración donde todos los coches aceleran."""
        self._tiempo_carrera += 1
        print(f"\n⏱️  TIEMPO: {self._tiempo_carrera}")
        print("-" * 70)
        
        for coche in self._coches:
            coche.acelerar()
            coche.monitorizar()
    
    def iniciar(self) -> None:
        """
        Inicia la simulación completa de la carrera.
        La carrera continúa hasta que algún coche complete la distancia meta.
        """
        if not self._coches:
            print(" No hay coches en la carrera")
            return
        
        print(f"\n{'='*70}")
        print(f" INICIO DE LA CARRERA: {self._nombre}")
        print(f" Distancia a recorrer: {self._distancia_meta} km")
        print(f" Participantes: {len(self._coches)} coches")
        print(f"{'='*70}\n")
        
        # Bucle principal de la carrera
        while not self.hay_ganador():
            if all(coche._combustible <= 0 for coche in self._coches):
                print("Ningún coche ha alcanzado la meta: se agotó el combustible.")
                return

            self.simular_vuelta()
            print("=====")
        
        # Carrera finalizada
        self._finalizada = True
        self._ganador = self.determinar_ganador()
        
        print(f"\n{'='*70}")
        print(f"🏆 ¡CARRERA FINALIZADA!")
        print(f"{'='*70}")
        print(f"🥇 GANADOR: {self._ganador._nombre}")
        print(f"   Distancia recorrida: {self._ganador.recorrido:.2f} km")
        print(f"   Combustible restante: {self._ganador._combustible:.2f}L")
        print(f"   Tiempo total: {self._tiempo_carrera} vueltas")
        print(f"{'='*70}\n")
        
        # Mostrar clasificación final
        self.mostrar_clasificacion()
    
    def reiniciar(self) -> None:
        """Reinicia la carrera a estado inicial."""
        self._tiempo_carrera = 0
        self._finalizada = False
        self._ganador = None
        
        for coche, combustible_inicial in zip(
            self._coches, self._combustible_inicial
        ):
            coche.tiempo = 0
            coche.recorrido = 0
            coche._combustible = combustible_inicial
        
        print(f"🔄 Carrera {self._nombre} reiniciada")
