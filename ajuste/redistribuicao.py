import pandas as pd

# Lógica de redistribuição por rodadas (greedy por pulmão)

def _rodada_once(df: pd.DataFrame) -> pd.DataFrame:
    # Listas (índice, valor) para doadores/recebedores
    doadores = [(i, int(df.loc[i, "sobra_disponivel"])) for i in df.index if df.loc[i, "sobra_disponivel"] > 0]
    recebedores = [(i, int(df.loc[i, "falta_necessaria"])) for i in df.index if df.loc[i, "falta_necessaria"] > 0]

    d_ptr, r_ptr = 0, 0
    df["_doar"] = 0
    df["_receber"] = 0

    while d_ptr < len(doadores) and r_ptr < len(recebedores):
        di, d_sobra = doadores[d_ptr]
        ri, r_falta = recebedores[r_ptr]
        if d_sobra == 0:
            d_ptr += 1
            continue
        if r_falta == 0:
            r_ptr += 1
            continue
        mov = min(d_sobra, r_falta)
        df.at[di, "sobra_disponivel"] -= mov
        df.at[ri, "falta_necessaria"] -= mov
        df.at[di, "_doar"] += mov
        df.at[ri, "_receber"] += mov
        doadores[d_ptr] = (di, d_sobra - mov)
        recebedores[r_ptr] = (ri, r_falta - mov)
        if doadores[d_ptr][1] == 0:
            d_ptr += 1
        if recebedores[r_ptr][1] == 0:
            r_ptr += 1

    return df


def redistribuir_em_rodadas(df: pd.DataFrame, n_rodadas: int = 3) -> pd.DataFrame:
    # Ordena por prioridade (pulmão)
    df = df.sort_values("pulmao", ascending=False).reset_index(drop=True)

    for idx_rod, rod_col in enumerate(["rod1", "rod2", "rod3"][:n_rodadas], start=1):
        df = _rodada_once(df)
        # aplica resultado da rodada
        df[rod_col] = df.get(rod_col, 0) - df["_doar"] + df["_receber"]
        df.drop(columns=["_doar", "_receber"], inplace=True)
        # Early stop se não há mais o que movimentar
        if (df["sobra_disponivel"].sum() == 0) or (df["falta_necessaria"].sum() == 0):
            break

    # Saídas finais
    df["final_reajustado"] = df["recebeu"] + df[["rod1", "rod2", "rod3"]].sum(axis=1)
    df["ajuste_total"] = df["final_reajustado"] - df["recebeu"]
    return df