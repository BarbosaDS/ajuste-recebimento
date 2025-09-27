from typing import Dict
from decimal import Decimal
import pandas as pd

def calcular_diferencas_basicas(row: Dict) -> Dict:
    """
    Mantém memória de cálculo em Decimal (sem arredondar para inteiro).
    Regras (iguais à planilha):
      falta = max(enviou - recebeu, 0)
      sobra = max(recebeu - enviou, 0)
      limites_atuais_% = 0 se enviou=0, senão (max(falta, sobra)/enviou)*100
      ajuste_% = max(limites_atuais_% - limite_admissivel_%, 0)
      ajuste_qtd (M) = (ajuste_% * enviou) / 100   # decimal, sem round p/ int
    """
    enviou  = Decimal(str(row.get("enviou", 0) or 0))
    recebeu = Decimal(str(row.get("recebeu", 0) or 0))
    lim     = Decimal(str(row.get("limite_admissivel_%", 0) or 0))  # 0.20 = 0,20 p.p.
    ZERO    = Decimal("0")

    falta_bruta = max(enviou - recebeu, ZERO)
    sobra_bruta = max(recebeu - enviou, ZERO)

    atuais_pct = ZERO if enviou == ZERO else (max(falta_bruta, sobra_bruta) / enviou) * Decimal("100")
    ajuste_pct = max(atuais_pct - lim, ZERO)
    ajuste_qtd = (ajuste_pct * enviou) / Decimal("100")  # mantém casas decimais

    sobra_disp = max(sobra_bruta - ajuste_qtd, ZERO)
    falta_need = max(falta_bruta - ajuste_qtd, ZERO)

    # Saída como float (para DF/Streamlit), mas o cálculo acima foi todo em Decimal
    return {
        **row,
        "falta": float(falta_bruta),
        "sobra": float(sobra_bruta),
        "limites_atuais_%": float(round(atuais_pct, 10)),
        "ajuste_%": float(round(ajuste_pct, 10)),
        "ajuste_qtd": float(ajuste_qtd),
        "sobra_disponivel": float(sobra_disp),
        "falta_necessaria": float(falta_need),
        "pulmao": float(abs(enviou - recebeu)),
        "rod1": 0.0,
        "rod2": 0.0,
        "rod3": 0.0,
    }

def preparar_dataframe(df_in: pd.DataFrame) -> pd.DataFrame:
    esperadas = ["produto", "enviou", "recebeu", "limite_admissivel_%"]
    for c in esperadas:
        if c not in df_in.columns:
            df_in[c] = 0
    reg_list = [calcular_diferencas_basicas(dict(r)) for _, r in df_in[esperadas].iterrows()]
    df = pd.DataFrame(reg_list)
    cols = [
        "produto","enviou","recebeu","limite_admissivel_%",
        "falta","sobra","limites_atuais_%","ajuste_%","ajuste_qtd",
        "sobra_disponivel","falta_necessaria","pulmao",
        "rod1","rod2","rod3"
    ]
    return df[cols]
