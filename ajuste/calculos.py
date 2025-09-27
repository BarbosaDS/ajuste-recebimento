from typing import Dict
import pandas as pd

# Regras elementares por linha

def linha_calc(row: Dict) -> Dict:
    enviou = float(row.get("enviou", 0) or 0)
    recebeu = float(row.get("recebeu", 0) or 0)
    lim = float(row.get("limite_admissivel_%", 0) or 0)  # em pontos percentuais (ex.: 0.20 = 0,20%)

    falta = max(enviou - recebeu, 0)
    sobra = max(recebeu - enviou, 0)

    atuais_pct = 0.0 if enviou == 0 else (max(falta, sobra) / enviou) * 100
    ajuste_pct = max(atuais_pct - lim, 0)
    ajuste_qtd = round((ajuste_pct * enviou) / 100)

    sobra_disp = max(sobra - ajuste_qtd, 0)
    falta_need = max(falta - ajuste_qtd, 0)

    return {
        **row,
        "falta": falta,
        "sobra": sobra,
        "limites_atuais_%": round(atuais_pct, 4),
        "ajuste_%": round(ajuste_pct, 4),
        "ajuste_qtd": int(ajuste_qtd),
        "sobra_disponivel": int(sobra_disp),
        "falta_necessaria": int(falta_need),
        "pulmao": abs(enviou - recebeu),
        "rod1": 0,
        "rod2": 0,
        "rod3": 0,
    }


def preparar_dataframe(df_in: pd.DataFrame) -> pd.DataFrame:
    # Normaliza colunas esperadas e aplica linha_calc
    esperadas = ["produto", "enviou", "recebeu", "limite_admissivel_%"]
    for c in esperadas:
        if c not in df_in.columns:
            df_in[c] = 0

    reg_list = [linha_calc(dict(r)) for _, r in df_in[esperadas].iterrows()]
    df = pd.DataFrame(reg_list)
    # garante ordem de colunas amigável
    cols = [
        "produto","enviou","recebeu","limite_admissivel_%",
        "falta","sobra","limites_atuais_%","ajuste_%","ajuste_qtd",
        "sobra_disponivel","falta_necessaria","pulmao",
        "rod1","rod2","rod3"
    ]
    return df[cols]