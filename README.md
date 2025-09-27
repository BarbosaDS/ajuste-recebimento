# Ajuste de Recebimento

App web (Streamlit) para aplicar regras de ajuste (falta/sobra, tolerância, redistribuição por pulmão em rodadas) e gerar o **valor final reajustado**.

## Como rodar local
```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy — Streamlit Community Cloud
1. Suba `streamlit_app.py` e a pasta `ajuste/` para um repositório GitHub.
2. Inclua `requirements.txt` na raiz.
3. Em https://share.streamlit.io → New app → selecione o repo e `streamlit_app.py`.

## Entrada mínima (por linha)
- `produto` (texto)
- `enviou` (número)
- `recebeu` (número)
- `limite_admissivel_%` (ex.: **0.20** para 0,20%)

## Saída
- `rod1`, `rod2`, `rod3`
- `final_reajustado` = `recebeu + rod1 + rod2 + rod3`
- `ajuste_total`

## Observações
- `limite_admissivel_%` está em **pontos percentuais** (0.20 = 0,20%).
- Arredondamento atual: `round()` na quantidade de ajuste.
- A redistribuição é **greedy** por *pulmão* (maior |D−E| primeiro) em até 3 rodadas.