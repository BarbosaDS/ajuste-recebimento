import pandas as pd
from ajuste.calculos import preparar_dataframe


def test_preparar_dataframe_basico():
    df_in = pd.DataFrame([
        {"produto": "A", "enviou": 100, "recebeu": 90,  "limite_admissivel_%": 0.20},
        {"produto": "B", "enviou": 100, "recebeu": 120, "limite_admissivel_%": 0.20},
    ])
    df = preparar_dataframe(df_in)
    assert set(["falta","sobra","ajuste_qtd"]).issubset(df.columns)
    # diferença bruta
    assert df.loc[0, "falta"] == 10
    assert df.loc[1, "sobra"] == 20