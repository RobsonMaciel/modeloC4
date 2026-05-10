import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from ai_extractor import ai_extract

st.set_page_config(page_title="C4 Studio Interno", page_icon="🧭", layout="wide")

st.title("🧭 C4 Studio Interno")
st.caption("Uso interno • Pipeline assistida por IA para geração de arquitetura C4")

with st.sidebar:
    st.header("Configuração")
    project_name = st.text_input("Nome do projeto", placeholder="ex: Plataforma de Pedidos")
    domain = st.selectbox("Domínio principal", ["E-commerce", "Financeiro", "SaaS", "Logística", "Outro"])
    level_scope = st.multiselect(
        "Níveis C4 para gerar",
        ["Nível 1 - Contexto", "Nível 2 - Containers", "Nível 3 - Componentes", "Deployment"],
        default=["Nível 1 - Contexto", "Nível 2 - Containers"],
    )
    strict_mode = st.toggle("Validação semântica rígida", value=True)

col1, col2 = st.columns([1.5, 1.0])

with col1:
    st.subheader("1) Entrada de documentação")
    docs = st.file_uploader(
        "Envie documentos do projeto",
        type=["md", "txt", "yaml", "yml", "json", "pdf"],
        accept_multiple_files=True,
    )

    if docs:
        st.success(f"{len(docs)} arquivo(s) carregado(s).")
        st.dataframe(
            [{"arquivo": d.name, "tipo": Path(d.name).suffix.replace('.', ''), "tamanho_kb": round(d.size / 1024, 2)} for d in docs],
            use_container_width=True,
            hide_index=True,
        )

with col2:
    st.subheader("Status da pipeline")
    st.write(f"{'✅' if docs else '⏳'} Ingestão")
    st.write(f"{'✅' if docs and project_name else '⏳'} Extração semântica")
    st.write(f"{'✅' if docs and project_name else '⏳'} Modelo canônico")

st.divider()
st.subheader("2) Gerar arquitetura")

if st.button("Gerar artefatos C4", type="primary", use_container_width=True):
    if not project_name or not docs:
        st.error("Preencha o nome do projeto e envie ao menos um documento.")
    else:
        parsed_docs = []
        for d in docs:
            try:
                parsed_docs.append((d.name, d.getvalue().decode("utf-8", errors="ignore")))
            except Exception:
                parsed_docs.append((d.name, ""))

        with st.spinner("Executando extração assistida por IA..."):
            extracted = ai_extract(parsed_docs, project_name, domain)

        canonical_model = {
            "project": project_name,
            "domain": domain,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "strict_mode": strict_mode,
            "levels": level_scope,
            **extracted,
            "source_files": [d.name for d in docs],
        }

        st.success("Arquitetura C4 gerada com sucesso.")
        st.json(canonical_model)
        st.download_button(
            "Baixar architecture-model.json",
            data=json.dumps(canonical_model, indent=2, ensure_ascii=False),
            file_name="architecture-model.json",
            mime="application/json",
            use_container_width=True,
        )
