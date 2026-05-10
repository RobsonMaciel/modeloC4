# Modelo C4 para documentação de arquiteturas

**Update:** Uma atualização foi feita no repositório e os modelos foram reescritos utilizando a ferramenta [Structurizr Lite](https://structurizr.com/help/lite).

Este repositório contém todos os diagramas contidos na apresentação do modelo C4.

[PlantUML](https://plantuml.com/) foi utilizado em conjunto com [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML) para gerar os diagramas.

---

## Como transformar este repositório em uma "fábrica" de arquitetura C4

Se o objetivo é **passar uma documentação de projeto** e receber do outro lado **toda a arquitetura C4 (Contexto, Containers, Componentes e opcionalmente Código/Deployment)**, recomendo evoluir este projeto para uma pipeline em 5 camadas:

### 1) Ingestão de documentação (entrada)

Crie uma interface padrão de entrada para receber documentação em formatos comuns:

- Markdown (`.md`)
- ADRs
- OpenAPI/Swagger
- README técnico
- Diagramas legados (opcional)
- Planilhas de integrações

**Saída desta camada:** um pacote normalizado por projeto, por exemplo:

```text
input/
  projeto-x/
    docs/*.md
    openapi/*.yaml
    adr/*.md
```

### 2) Extração semântica (NLP + regras)

A partir da documentação, extraia os elementos fundamentais do C4:

- **Pessoas** (atores)
- **Sistemas externos**
- **Sistema alvo**
- **Containers** (apps, APIs, filas, banco, etc.)
- **Componentes internos**
- **Relações** (quem usa quem, protocolo, direção)

Esse passo pode ser híbrido:

- **Regras determinísticas** (regex/keywords para termos técnicos)
- **LLM** para desambiguação semântica
- **Validação por schema** (JSON Schema) para evitar saída inválida

**Saída desta camada:** um `architecture-model.json` canônico.

### 3) Modelo intermediário canônico (core do projeto)

Adicione um formato intermediário único para desacoplar extração e renderização. Exemplo de estrutura:

```json
{
  "system": "E-commerce Platform",
  "actors": [],
  "externalSystems": [],
  "containers": [],
  "components": [],
  "relationships": []
}
```

Esse modelo deve suportar:

- rastreabilidade da origem (`source_ref` da documentação)
- confiança da extração (`confidence_score`)
- tags de domínio (`billing`, `auth`, `orders`)

### 4) Geradores C4 (Structurizr DSL + PlantUML)

Crie geradores automáticos que leem o `architecture-model.json` e produzem:

- `workspace.dsl` (Structurizr)
- `context.puml`
- `containers.puml`
- `components-*.puml`
- `deployment.puml` (quando houver dados de infraestrutura)

Isso permite manter o que este repositório já tem de bom (exemplos visuais) e incluir geração 100% automática.

### 5) Orquestração + revisão humana

Fluxo recomendado para uso real:

1. Usuário envia documentação.
2. Pipeline extrai e gera C4 automaticamente.
3. Sistema aponta ambiguidades (ex.: "não ficou claro se Redis é cache ou fila").
4. Usuário responde perguntas curtas.
5. Pipeline regenera os diagramas finais.

Isso mantém o processo natural para times não especialistas e reduz erro semântico.

---

## Roadmap prático (MVP em 3 fases)

### Fase 1 — Fundacional

- Definir schema `architecture-model.json`
- Criar parser inicial de Markdown/ADRs
- Gerar somente **Nível 1 (Contexto)** e **Nível 2 (Containers)**

### Fase 2 — Escala

- Adicionar ingestão de OpenAPI
- Incluir Nível 3 (Componentes)
- Introduzir validações automáticas (regras de arquitetura)

### Fase 3 — Produto interno

- Criar CLI (`c4gen`) e/ou interface web
- Publicar templates por tipo de sistema (monolito, microserviços, event-driven)
- CI para gerar e versionar diagramas por commit

---

## Estrutura sugerida para este repositório

```text
modeloC4/
  examples/                    # exemplos atuais (conteúdo já existente)
  engine/
    ingest/
    extract/
    model/
    generators/
    validation/
  schemas/
    architecture-model.schema.json
  templates/
    structurizr/
    plantuml/
  cli/
    c4gen
```

---

## Critérios de qualidade para “C4 automático”

Para funcionar bem em qualquer projeto, defina métricas objetivas:

- **Cobertura:** % de requisitos/documentos refletidos em elementos C4
- **Consistência:** relações semânticas válidas (ex.: ator não escreve direto no banco)
- **Legibilidade:** limite de elementos por diagrama
- **Rastreabilidade:** cada elemento aponta para trecho de documentação fonte
- **Tempo de geração:** alvo de segundos/minutos por projeto

---


## Interface interna (MVP)

Para iniciar uma interface profissional de uso interno, foi adicionado um MVP com Streamlit em `internal_app/`.

### Executando

```bash
pip install -r internal_app/requirements.txt
streamlit run internal_app/app.py
```

### O que o MVP já entrega

- formulário para configuração do projeto
- upload de documentação técnica
- status visual da pipeline
- geração de preview do `architecture-model.json`
- exportação do modelo canônico

### Configuração de IA (opcional, recomendado)

O app pode usar uma API de IA compatível com Chat Completions para melhorar a extração semântica.

```bash
export C4_AI_API_KEY="..."
export C4_AI_MODEL="gpt-4.1-mini"
export C4_AI_BASE_URL="https://api.openai.com/v1"
export C4_AI_TIMEOUT_SEC="90"
```

Sem essas variáveis, o sistema usa extração heurística local (fallback).


## Gerando os diagramas

### Structurizr lite

Escrevi uma função para facilitar a utilização do comando:

```bash
# structurizr
function structurizr() {
    readonly file=${1:?"The workspace filename must be specified."}
    if [[ "$file" == *.* ]]; then
        echo "The workspace filename should not contains a file extension."
        return 1
    fi
    if [[ !  -f "./structurizr.properties" ]]; then
        echo "structurizr.autoRefreshInterval=2000" > structurizr.properties
    fi
    docker run --rm -it \
        -p 8080:8080 \
        -u $(id -u ${USER}):$(id -g ${USER}) \
        -v "$PWD":/usr/local/structurizr/ \
        -e STRUCTURIZR_WORKSPACE_FILENAME=$file \
            structurizr/lite
}
```

Ela será invocada da seguinte maneira:

```bash
structurizr nome_do_arquivo_sem_extensão
```

### PlantUML

O [VS Code](https://code.visualstudio.com/) possui um plugin para PlantUML que pode ser encontrado na marketplace: [PlantUML for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml).

Caso queira rodar localmente será necessário instalar o [Graphviz](https://www.graphviz.org/). No sistema operacional ubuntu o comando é:

    sudo apt-get install graphviz openjdk-17-jre

Os diagramas também podem ser gerados utilizando o servidor remoto: http://www.plantuml.com/plantuml/uml/.

Abra os arquivos de extensão `.puml` ou copie seu conteúdo para o editor ou navegador.

Caso esteja utilizando a versão online, clique no botão `Render` para gerar a imagem.

Se estiver rodando localmente, aperte `ALT + D` para ter uma pré visualização, ou `CTRL + SHIFT + P` e selecione a opção de exportar a imagem ou pré visualização.
