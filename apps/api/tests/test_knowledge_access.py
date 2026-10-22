from fraudlens.auth import Principal
from fraudlens.config import Settings
from fraudlens.knowledge import load_knowledge, retrieve_knowledge


def test_knowledge_retrieval_respects_roles_and_excludes_proposals(tmp_path, monkeypatch):
    common = "title: Upload help\nroute: /uploads\nstatus: implemented\n"
    (tmp_path / "public.md").write_text(
        "---\nid: uploads\nroles: [viewer, admin]\n"
        + common
        + "---\n# Upload files\nSupported upload file types are documented.",
        encoding="utf-8",
    )
    (tmp_path / "private.md").write_text(
        "---\nid: private\nroles: [admin]\n"
        + common
        + "---\n# Upload files\nAdmin restricted configuration.",
        encoding="utf-8",
    )
    (tmp_path / "proposal.md").write_text(
        "---\nid: proposed\nroles: [viewer]\nstatus: proposed\n---\n# Upload\nProposed only.",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "fraudlens.knowledge.get_settings",
        lambda: Settings(_env_file=None, knowledge_base_path=str(tmp_path)),
    )
    viewer = Principal(subject="reader", tenant_id="alpha", roles={"viewer"})
    chunks = retrieve_knowledge("upload files", viewer, "/uploads")
    assert {chunk.document_id for chunk in chunks} == {"uploads"}
    admin = Principal(subject="admin", tenant_id="beta", roles={"admin"})
    assert {chunk.document_id for chunk in retrieve_knowledge("upload files", admin)} == {
        "uploads",
        "private",
    }
    assert retrieve_knowledge("unrelatedzebra", viewer) == []
    load_knowledge.cache_clear()
