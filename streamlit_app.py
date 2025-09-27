import io
import pandas as pd
import streamlit as st
from ajuste.calculos import linha_calc, preparar_dataframe
from ajuste.redistribuicao import redistribuir_em_rodadas

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

        **Regras implementadas**:
        - Calcula **falta**, **sobra**, **% atual** vs. enviado, aplica **tolerância**, converte para **ajuste em quantidade**.
        - Redistribuição **greedy por pulmão** (maior |enviou−recebeu| primeiro) em até **3 rodadas** (`rod1`, `rod2`, `rod3`).
        - Saída: **final_reajustado** = `recebeu + rod1 + rod2 + rod3` e `ajuste_total`.
        """
    )

# ----------------------------
# UI — Por item
# ----------------------------
col1, col2, col3, col4 = st.columns([2,1,1,1])
with col1:
    produto = st.text_input("produto", value="")
with col2:
    enviou = st.number_input("enviou", min_value=0.0, value=0.0, step=1.0)
with col3:
    recebeu = st.number_input("recebeu", min_value=0.0, value=0.0, step=1.0)
with col4:
    limite = st.number_input("limite_admissivel_%", min_value=0.0, value=0.20, step=0.01, help="0.20 = tolerância de 0,20% (pontos percentuais)")

if st.button("Calcular (1 item)"):
    base = pd.DataFrame([{"produto": produto, "enviou": enviou, "recebeu": recebeu, "limite_admissivel_%": limite}])
    df = preparar_dataframe(base)
    df_out = redistribuir_em_rodadas(df.copy())
    st.subheader("Resultado — 1 item")
    st.dataframe(df_out[[
        "produto","enviou","recebeu","limite_admissivel_%",
        "falta","sobra","limites_atuais_%","ajuste_%","ajuste_qtd",
        "sobra_disponivel","falta_necessaria","rod1","rod2","rod3",
        "final_reajustado","ajuste_total"
    ]], use_container_width=True)

st.markdown("---")

# ----------------------------
# UI — Em lote (CSV/XLSX)
# ----------------------------

st.subheader("Em lote (CSV/XLSX)")

# Template de exemplo (gerado em memória)
example = pd.DataFrame([
    {"produto": "A", "enviou": 100, "recebeu": 90,  "limite_admissivel_%": 0.20},
    {"produto": "B", "enviou": 100, "recebeu": 120, "limite_admissivel_%": 0.20},
    {"produto": "C", "enviou": 80,  "recebeu": 70,  "limite_admissivel_%": 0.20},
])

buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
    example.to_excel(writer, index=False, sheet_name="entrada")
    ws = writer.book.add_worksheet("leia_me")
    ws.write("A1", "Preencha a aba 'entrada' com as colunas: produto, enviou, recebeu, limite_admissivel_%.")
    ws.write("A2", "Envie o arquivo aqui embaixo para calcular as colunas e as rodadas.")

st.download_button("Baixar template.xlsx", data=buf.getvalue(), file_name="template_entrada.xlsx")

up = st.file_uploader("Envie um CSV ou XLSX com as colunas mínimas", type=["csv","xlsx"])
if up:
    if up.name.endswith(".csv"):
        df_in = pd.read_csv(up)
    else:
        df_in = pd.read_excel(up)

    esperadas = ["produto","enviou","recebeu","limite_admissivel_%"]
    faltantes = [c for c in esperadas if c not in df_in.columns]
    if faltantes:
        st.error(f"Colunas faltando: {faltantes}. Use o template.")
    else:
        df = preparar_dataframe(df_in)
        df_out = redistribuir_em_rodadas(df.copy())
        st.success("Cálculo concluído.")
        st.dataframe(df_out, use_container_width=True)

        # Download de saída
        out_buf = io.BytesIO()
        with pd.ExcelWriter(out_buf, engine="xlsxwriter") as writer:
            df_out.to_excel(writer, index=False, sheet_name="resultado")
        st.download_button("Baixar resultado.xlsx", data=out_buf.getvalue(), file_name="resultado_ajuste.xlsx")