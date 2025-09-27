import math

# Coloque aqui utilitários de arredondamento/cap, se precisar no futuro.
# Ex.: sempre para baixo/para cima nos ajustes, caps por produto, etc.


def round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))