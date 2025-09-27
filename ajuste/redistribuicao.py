from typing import Dict, Tuple
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

def _to_dec(x) -> Decimal:
    return Decimal(str(x if x is not None else 0))

def _extrair_basicos(item: Dict) -> Tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
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

def _q2(v: Decimal) -> Decimal:
    """Quantiza em 2 casas (igual planilha)."""
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calcular_rods_para_par(a: Dict, b: Dict) -> Tuple[Dict, Dict]:
    """
    RODs CUMULATIVOS (espelho da planilha):
      N = M_recebedor (cap: N <= sobra_doador)
      O12 = |N - G_recebedor|
      Q = N + O12
      T = Q + O12
    Saída:
      doador:  rod1=-N, rod2=-Q, rod3=-T
      recebedor: rod1=+N, rod2=+Q, rod3=+T
      final_reajustado = recebeu ± rod3 (cumulativo)
    """
    aF, bF = float(max(a.get("sobra", 0), 0)), float(max(b.get("sobra", 0), 0))
    aG, bG = float(max(a.get("falta", 0), 0)), float(max(b.get("falta", 0), 0))

    # Sem par válido (ambos sobra ou ambos falta)
    if (aF == 0 and bF == 0) or (aG == 0 and bG == 0):
        for x in (a, b):
            x.update({"rod1": 0.0, "rod2": 0.0, "rod3": 0.0,
                      "final_reajustado": float(x.get("recebeu", 0)), "ajuste_total": 0.0})
        return a, b

    if aF > 0 and bG > 0:
        doador, recebedor = a.copy(), b.copy()
        order = ("a", "b")
    elif bF > 0 and aG > 0:
        doador, recebedor = b.copy(), a.copy()
        order = ("b", "a")
    else:
        for x in (a, b):
            x.update({"rod1": 0.0, "rod2": 0.0, "rod3": 0.0,
                      "final_reajustado": float(x.get("recebeu", 0)), "ajuste_total": 0.0})
        return a, b

    Dd, Ed, Fd, _, _  = _extrair_basicos(doador)
    Dr, Er, _, Gr, Mr = _extrair_basicos(recebedor)

    # ROD1 (N) = M_recebedor com CAP na sobra do doador
    N  = min(Mr, Fd)
    O12 = abs(N - Gr)            # falta residual do recebedor após ROD1
    Q  = N + O12                 # ROD2 (cumulativo)
    T  = Q + O12                 # ROD3 (cumulativo)

    # Cumulativos com 2 casas
    Nq, Qq, Tq = _q2(N), _q2(Q), _q2(T)

    # Atribui (doador negativo, recebedor positivo)
    ad = doador.copy()
    ar = recebedor.copy()

    ad.update({"rod1": float(-Nq), "rod2": float(-Qq), "rod3": float(-Tq)})
    ar.update({"rod1": float(+Nq), "rod2": float(+Qq), "rod3": float(+Tq)})

    # final após rod3 = recebeu ± rod3 (cumulativo)
    ad["final_reajustado"] = float(_to_dec(ad["recebeu"]) - Tq)
    ar["final_reajustado"] = float(_to_dec(ar["recebeu"]) + Tq)
    ad["ajuste_total"] = float(-Tq)
    ar["ajuste_total"] = float(+Tq)

    # devolver na ordem original (a, b)
    if order == ("a", "b"):
        return ad, ar
    else:
        return ar, ad

def parear_e_aplicar_rods(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pareia doadores (sobra>0) e recebedores (falta>0) por 'pulmão'
    e aplica calcular_rods_para_par() em cada par.
    Itens não pareados: final = recebeu; ajuste_total = 0.
    """
    out = df.copy()
    for c in ["rod1", "rod2", "rod3", "final_reajustado", "ajuste_total"]:
        if c not in out.columns:
            out[c] = 0.0

    doadores = out.index[out["sobra"] > 0].tolist()
    recebedores = out.index[out["falta"] > 0].tolist()
    doadores.sort(key=lambda i: out.loc[i, "pulmao"], reverse=True)
    recebedores.sort(key=lambda i: out.loc[i, "pulmao"], reverse=True)

    for i, j in zip(doadores, recebedores):
        ai = out.loc[i].to_dict()
        bj = out.loc[j].to_dict()
        ra, rb = calcular_rods_para_par(ai, bj)
        for k, r in zip([i, j], [ra, rb]):
            out.at[k, "rod1"] = r["rod1"]
            out.at[k, "rod2"] = r["rod2"]
            out.at[k, "rod3"] = r["rod3"]
            out.at[k, "final_reajustado"] = r["final_reajustado"]
            out.at[k, "ajuste_total"] = r["ajuste_total"]

    # itens não pareados
    mask = out["final_reajustado"].isna()
    out.loc[mask, "final_reajustado"] = out.loc[mask, "recebeu"]
    out.loc[mask, "ajuste_total"] = 0.0
    return out
