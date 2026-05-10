import json
import os
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class AISettings:
    api_key: str | None
    model: str
    base_url: str
    timeout_sec: int = 90


SYSTEM_PROMPT = (
    "Você é um arquiteto de software especialista em C4. "
    "Converta a documentação recebida para um JSON canônico com as chaves: "
    "actors, externalSystems, containers, components, relationships, assumptions, questions. "
    "Responda apenas JSON válido."
)


def load_settings() -> AISettings:
    return AISettings(
        api_key=os.getenv("C4_AI_API_KEY"),
        model=os.getenv("C4_AI_MODEL", "gpt-4.1-mini"),
        base_url=os.getenv("C4_AI_BASE_URL", "https://api.openai.com/v1"),
        timeout_sec=int(os.getenv("C4_AI_TIMEOUT_SEC", "90")),
    )


def _join_docs(files: list[tuple[str, str]], max_chars: int = 60000) -> str:
    chunks: list[str] = []
    size = 0
    for name, content in files:
        block = f"\n\n# Arquivo: {name}\n{content.strip()}"
        if size + len(block) > max_chars:
            break
        chunks.append(block)
        size += len(block)
    return "".join(chunks)


def heuristic_extract(files: list[tuple[str, str]]) -> dict[str, Any]:
    """Fallback determinístico quando a API de IA não está configurada."""
    names = [name for name, _ in files]
    containers = []
    relationships = []
    if any("openapi" in n.lower() or n.endswith((".yaml", ".yml")) for n in names):
        containers.append({"name": "API Service", "technology": "HTTP/REST", "description": "API identificada por documentação."})
    if any("readme" in n.lower() or n.endswith(".md") for n in names):
        containers.append({"name": "Aplicação Principal", "technology": "A definir", "description": "Aplicação descrita na documentação."})
    if containers:
        relationships.append({"from": "Usuário", "to": containers[0]["name"], "description": "Usa funcionalidades do sistema"})
    return {
        "actors": [{"name": "Usuário", "description": "Ator padrão inferido"}],
        "externalSystems": [],
        "containers": containers,
        "components": [],
        "relationships": relationships,
        "assumptions": ["Extração heurística por falta de configuração de IA."],
        "questions": ["Quais bancos, filas e sistemas externos devem ser adicionados?"],
    }


def ai_extract(files: list[tuple[str, str]], project_name: str, domain: str) -> dict[str, Any]:
    settings = load_settings()
    if not settings.api_key:
        return heuristic_extract(files)

    user_prompt = {
        "project": project_name,
        "domain": domain,
        "docs": _join_docs(files),
        "instructions": "Preencha todos os campos com listas, mesmo que vazias.",
    }

    payload = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }

    resp = requests.post(
        f"{settings.base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=settings.timeout_sec,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)
