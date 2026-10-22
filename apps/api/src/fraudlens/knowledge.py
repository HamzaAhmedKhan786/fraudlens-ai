import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fraudlens.auth import Principal
from fraudlens.config import get_settings

TOKEN = re.compile(r"[a-z0-9]{2,}")


@dataclass(frozen=True)
class KnowledgeChunk:
    document_id: str
    title: str
    section: str
    route: str | None
    roles: frozenset[str]
    content: str
    revision: str


def _metadata(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---"):
        return {}, raw
    _, header, body = raw.split("---", 2)
    values: dict[str, str] = {}
    for line in header.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()
    return values, body.strip()


def _roles(value: str) -> frozenset[str]:
    return frozenset(x.strip() for x in value.strip("[]").split(",") if x.strip())


@lru_cache(maxsize=4)
def load_knowledge(path_value: str) -> tuple[KnowledgeChunk, ...]:
    root = Path(path_value)
    if not root.is_absolute():
        root = Path.cwd() / root
    chunks: list[KnowledgeChunk] = []
    if not root.exists():
        return ()
    for path in sorted(root.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        metadata, body = _metadata(raw)
        if metadata.get("status", "").startswith("proposed"):
            continue
        document_id = metadata.get("id", path.stem)
        title = metadata.get("title", path.stem)
        revision = hashlib.sha256(raw.encode()).hexdigest()[:12]
        section = title
        content: list[str] = []
        for line in body.splitlines():
            if line.startswith("# ") or line.startswith("## "):
                if content:
                    chunks.append(
                        KnowledgeChunk(
                            document_id,
                            title,
                            section,
                            metadata.get("route"),
                            _roles(metadata.get("roles", "")),
                            "\n".join(content).strip(),
                            revision,
                        )
                    )
                section, content = line.lstrip("# ").strip(), []
            else:
                content.append(line)
        if content:
            chunks.append(
                KnowledgeChunk(
                    document_id,
                    title,
                    section,
                    metadata.get("route"),
                    _roles(metadata.get("roles", "")),
                    "\n".join(content).strip(),
                    revision,
                )
            )
    return tuple(chunk for chunk in chunks if chunk.content)


def retrieve_knowledge(
    query: str, principal: Principal, current_path: str | None = None
) -> list[KnowledgeChunk]:
    settings = get_settings()
    query_tokens = set(TOKEN.findall(query.lower()))
    if not query_tokens:
        return []
    roles = set(principal.roles)
    ranked: list[tuple[float, KnowledgeChunk]] = []
    for chunk in load_knowledge(settings.knowledge_base_path):
        if chunk.roles and not roles.intersection(chunk.roles):
            continue
        heading_tokens = set(TOKEN.findall(f"{chunk.title} {chunk.section}".lower()))
        body_tokens = set(TOKEN.findall(chunk.content.lower()))
        score = 2 * len(query_tokens & heading_tokens) + len(query_tokens & body_tokens)
        score /= max(len(query_tokens), 1)
        if score >= settings.knowledge_min_relevance:
            if current_path and chunk.route == current_path:
                score += 0.35
            ranked.append((score, chunk))
    ranked.sort(key=lambda item: (-item[0], item[1].document_id, item[1].section))
    return [chunk for _, chunk in ranked[: settings.knowledge_max_chunks]]
