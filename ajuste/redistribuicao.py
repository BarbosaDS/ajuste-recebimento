from typing import Dict, Tuple
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

def _to_dec(x) -> Decimal:
    return Decimal(str(x if x is not None else 0))

def _q2(v: Decimal) -> Decimal:
    """Quantiza em 2 casas decimais (como a planilha exibe)."""
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _extrair_basicos(item: Dict):
    """
    D = enviou
    E = recebeu
    F = sobra bruta = max(E-D, 0)
    G = falta bruta = max(D-E, 0)
    M = ajuste_qtd (do recebedor)
    """
    D = _to_dec(item.get("enviou"))
    E = _to_dec(item.get("recebeu"))
    ZERO = Decimal("0")
    F = max(E - D, ZERO)
    G = max(D - E, ZERO)
    M = _to_dec(item.get("ajuste_qtd"))
    return D, E, F, G, M

def calcular_rods_para_par(a: Dict, b: Dict) -> Tuple[Dict, Dict]:
    """
    >>> Versão simplificada: apenas o primeiro ajuste baseado no limite admissível.
    - quantidade_transferida (N) = min(M_recebedor, sobra_doador)
    - ajuste_item (O):
        doador   = |F - N|
        recebedor= |N - G|
    - novo_limite_% (P):
        doador   = (O_doador / D_doador) * 100
        recebedor= (O_recebedor / D_recebedor) * 100
    - final_reajustado = recebeu ± N
    """
    aF, bF = float(max(a.get("sobra", 0), 0)), float(max(b.get("sobra", 0), 0))
    aG, bG = float(max(a.get("falta", 0), 0)), float(max(b.get("falta", 0), 0))

    # Sem par válido → ninguém transfere
    if (aF == 0 and bF == 0) or (aG == 0 and bG == 0):
        for x in (a, b):
            x.update({
                "quantidade_transferida": 0.0,
                "ajuste_item": 0.0,
                "novo_limite_%": float(0),
                "final_reajustado": float(x.get("recebeu", 0)),
                "ajuste_total": 0.0,
            })
        return a, b

    # Define papéis
    if aF > 0 and bG > 0:
        doador, recebedor = a.copy(), b.copy()
        ordem = ("a", "b")
    elif bF > 0 and aG > 0:
        doador, recebedor = b.copy(), a.copy()
        ordem = ("b", "a")
    else:
        for x in (a, b):
            x.update({
                "quantidade_transferida": 0.0,
                "ajuste_item": 0.0,
                "novo_limite_%": float(0),
                "final_reajustado": float(x.get("recebeu", 0)),
                "ajuste_total": 0.0,
            })
        return a, b

    # Memória de cálculo (igual planilha)
    Dd, Ed, Fd, _, _  = _extrair_basicos(doador)
    Dr, Er, _, Gr, Mr = _extrair_basicos(recebedor)

    # N = min(M_recebedor, sobra_doador)
    N = min(Mr, Fd)
    Nq = _q2(N)

    # O (residual após o ajuste)
    Od = abs(Fd - N)   # doador
    Or = abs(N - Gr)   # recebedor
    Odq, Orq = _q2(Od), _q2(Or)

    # P (novo limite em %)
    Pd = Decimal("0") if Dd == 0 else (Od / Dd) * Decimal("100")
    Pr = Decimal("0") if Dr == 0 else (Or / Dr) * Decimal("100")
    Pdq, Prq = _q2(Pd), _q2(Pr)

    # Aplicar resultados
    ad = doador.copy()
    ar = recebedor.copy()

    ad.update({
        "quantidade_transferida": float(-Nq),  # doador doa (negativo)
        "ajuste_item": float(Odq),
        "novo_limite_%": float(Pdq),
        "final_reajustado": float(_to_dec(ad["recebeu"]) - Nq),
        "ajuste_total": float(-Nq),
    })
    ar.update({
        "quantidade_transferida": float(+Nq),  # recebedor recebe (positivo)
        "ajuste_item": float(Orq),
        "novo_limite_%": float(Prq),
        "final_reajustado": float(_to_dec(ar["recebeu"]) + Nq),
        "ajuste_total": float(+Nq),
    })

    # Devolver na ordem original (a, b)
    if ordem == ("a", "b"):
        return ad, ar
    else:
        return ar, ad

def parear_e_aplicar_rods(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pareia doadores (sobra>0) e recebedores (falta>0) por prioridade (pulmão)
    e aplica calcular_rods_para_par() em cada par.
    """
    out = df.copy()

    doadores = out.index[out["sobra"] > 0].tolist()
    recebedores = out.index[out["falta"] > 0].tolist()
    doadores.sort(key=lambda i: out.loc[i, "pulmao"], reverse=True)
    recebedores.sort(key=lambda i: out.loc[i, "pulmao"], reverse=True)

    for i, j in zip(doadores, recebedores):
        ai = out.loc[i].to_dict()
        bj = out.loc[j].to_dict()
        ra, rb = calcular_rods_para_par(ai, bj)
        for k, r in zip([i, j], [ra, rb]):
            for c in ["quantidade_transferida", "ajuste_item", "novo_limite_%",
                      "final_reajustado", "ajuste_total"]:
                out.at[k, c] = r[c]

    # Itens não pareados: mantém recebido como final
    mask = out["final_reajustado"].isna()
    out.loc[mask, "final_reajustado"] = out.loc[mask, "recebeu"]
    out.loc[mask, "ajuste_total"] = 0.0
    out.loc[mask, "quantidade_transferida"] = 0.0
    out.loc[mask, "ajuste_item"] = 0.0
    out.loc[mask, "novo_limite_%"] = 0.0

    return out
