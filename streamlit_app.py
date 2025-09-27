import io
import pandas as pd
import streamlit as st
from ajuste.calculos import preparar_dataframe
from ajuste.redistribuicao import calcular_rods_para_par, parear_e_aplicar_rods

st.set_page_config(page_title="Ajuste de Recebimento", layout="wide")

st.title("Ajuste de Recebimento")
st.caption("Entradas simples → cálculo Python → saída com valores finais")

with st.expander("📘 Como usar", expanded=True):
    st.markdown(
        """
        **Campos mínimos por linha**:
        - `produto` (texto)
        - `enviou` (número)
        - `recebeu` (número)
        - `limite_admissivel_%` (ex.: **0.20** para 0,20%)

        **Como funciona:**
        - Calculamos **sobra** e **falta** por linha.
        - O **ajuste em quantidade (M)** do recebedor vira **ROD1 = N** no doador (com cap pela sobra do doador).
        - **RODs são cumulativos**: `ROD1 = N`, `ROD2 = Q = N + O12`, `ROD3 = T = Q + O12`.
        - `final_reajustado` usa o **ROD3** (cumulativo): `recebeu ± T`.
        - Sinais: doador **negativo** (doa), recebedor **positivo** (recebe).
        """
    )

# ============================
# UI — Par 1×1 (duas linhas)
# ============================
st.subheader("Calcular para **2 itens** (par)")
col = st.columns([2, 1, 1, 1])
with col[0]:
    prod_a = st.text_input("produto A", value="")
with col[1]:
    enviou_a = st.number_input("enviou A", min_value=0.0, value=0.0, step=1.0)
with col[2]:
    recebeu_a = st.number_input("recebeu A", min_value=0.0, value=0.0, step=1.0)
with col[3]:
    lim_a = st.number_input("limite_admissivel_% A", min_value=0.0, value=0.20, step=0.01)

col = st.columns([2, 1, 1, 1])
with col[0]:
    prod_b = st.text_input("produto B", value="")
with col[1]:
    enviou_b = st.number_input("enviou B", min_value=0.0, value=0.0, step=1.0)
with col[2]:
    recebeu_b = st.number_input("recebeu B", min_value=0.0, value=0.0, step=1.0)
with col[3]:
    lim_b = st.number_input("limite_admissivel_% B", min_value=0.0, value=0.20, step=0.01)

if st.button("Calcular par (A ↔ B)"):
    base = pd.DataFrame(
        [
            {"produto": prod_a, "enviou": enviou_a, "recebeu": recebeu_a, "limite_admissivel_%": lim_a},
            {"produto": prod_b, "enviou": enviou_b, "recebeu": recebeu_b, "limite_admissivel_%": lim_b},
        ]
    )
    df = preparar_dataframe(base)
    a, b = df.iloc[0].to_dict(), df.iloc[1].to_dict()
    res_a, res_b = calcular_rods_para_par(a, b)
    out = pd.DataFrame([res_a, res_b])

    mostrar = out[
        [
            "produto",
            "enviou",
            "recebeu",
            "limite_admissivel_%",
            "falta",
            "sobra",
            "limites_atuais_%",
            "ajuste_%",
            "ajuste_qtd",
            "rod1",
            "rod2",
            "rod3",
            "final_reajustado",
            "ajuste_total",
        ]
    ].copy()
    num = [
        "enviou",
        "recebeu",
        "limite_admissivel_%",
        "falta",
        "sobra",
        "limites_atuais_%",
        "ajuste_%",
        "ajuste_qtd",
        "rod1",
        "rod2",
        "rod3",
        "final_reajustado",
        "ajuste_total",
    ]
    mostrar[num] = mostrar[num].applymap(lambda x: round(float(x), 2))
    st.dataframe(mostrar, use_container_width=True)

st.markdown("---")

# ============================
# UI — Em lote (CSV/XLSX)
# ============================
st.subheader("Em lote (CSV/XLSX)")

example = pd.DataFrame(
    [
        {"produto": "A", "enviou": 100, "recebeu": 120, "limite_admissivel_%": 0.20},
        {"produto": "B", "enviou": 100, "recebeu": 90, "limite_admissivel_%": 0.20},
        {"produto": "C", "enviou": 80, "recebeu": 70, "limite_admissivel_%": 0.20},
        {"produto": "D", "enviou": 200, "recebeu": 210, "limite_admissivel_%": 0.20},
    ]
)

buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
    example.to_excel(writer, index=False, sheet_name="entrada")
st.download_button("Baixar template.xlsx", data=buf.getvalue(), file_name="template_entrada.xlsx")

up = st.file_uploader("Envie um CSV ou XLSX com as colunas mínimas", type=["csv", "xlsx"])
if up:
    if up.name.endswith(".csv"):
        df_in = pd.read_csv(up)
    else:
        df_in = pd.read_excel(up)

    esperadas = ["produto", "enviou", "recebeu", "limite_admissivel_%"]
    faltantes = [c for c in esperadas if c not in df_in.columns]
    if faltantes:
        st.error(f"Colunas faltando: {faltantes}. Use o template.")
    else:
        # coerção numérica e limpeza básica
        for c in ["enviou", "recebeu", "limite_admissivel_%"]:
            df_in[c] = pd.to_numeric(df_in[c], errors="coerce")
        df_in = df_in.dropna(subset=["enviou", "recebeu", "limite_admissivel_%"])

        df = preparar_dataframe(df_in)
        df_out = parear_e_aplicar_rods(df)

        # formatar com 2 casas
        out = df_out.copy()
        num_cols = [
            "enviou",
            "recebeu",
            "limite_admissivel_%",
            "falta",
            "sobra",
            "limites_atuais_%",
            "ajuste_%",
            "ajuste_qtd",
            "rod1",
            "rod2",
            "rod3",
            "final_reajustado",
            "ajuste_total",
        ]
        out[num_cols] = out[num_cols].applymap(lambda x: round(float(x), 2))

        st.success("Cálculo concluído.")
        st.dataframe(out, use_container_width=True)

        out_buf = io.BytesIO()
        with pd.ExcelWriter(out_buf, engine="xlsxwriter") as writer:
            out.to_excel(writer, index=False, sheet_name="resultado")
        st.download_button("Baixar resultado.xlsx", data=out_buf.getvalue(), file_name="resultado_ajuste.xlsx")
