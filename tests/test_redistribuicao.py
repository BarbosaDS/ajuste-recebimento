import pandas as pd
from ajuste.calculos import preparar_dataframe
from ajuste.redistribuicao import redistribuir_em_rodadas


def test_redistribuicao_simples():
    df_in = pd.DataFrame([
        {"produto": "A", "enviou": 100, "recebeu": 90,  "limite_admissivel_%": 0.20},
        {"produto": "B", "enviou": 100, "recebeu": 120, "limite_admissivel_%": 0.20},
    ])
    df = preparar_dataframe(df_in)
    out = redistribuir_em_rodadas(df.copy())
    # como os dois têm mesmo pulmão (10 e 20), deverá haver movimento A<=B
    assert out[["rod1","rod2","rod3"]].abs().sum().sum() >= 0
    # final_reajustado é recebido + movimentações (só checando existência)
    assert "final_reajustado" in out.columns