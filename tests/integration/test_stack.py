"""End-to-end smoke test: Open WebUI + model backend + pgvector RAG.

Expects the stack to be running (see scripts/test-integration.sh).
"""

import os
import time

import pytest
import requests

BASE = os.environ.get("WEBUI_BASE", "http://localhost:3000")
MODEL = os.environ.get("TEST_MODEL", "qwen3:1.7b")
EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@orgos.test")
PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "ci-admin-test-pass")

# A fact the model cannot know without retrieving the uploaded document.
SECRET_FACT = "The ORGOS vault access code is ZEBRA-7731."


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE}/api/v1/auths/signup",
                      json={"name": "CI Admin", "email": EMAIL, "password": PASSWORD}, timeout=30)
    if r.status_code != 200:  # already exists on a reused DB
        r = requests.post(f"{BASE}/api/v1/auths/signin",
                          json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture(scope="session")
def auth(token):
    return {"Authorization": f"Bearer {token}"}


def chat(auth, content, **extra):
    r = requests.post(f"{BASE}/api/chat/completions", headers=auth, timeout=600, json={
        "model": MODEL,
        "stream": False,
        "messages": [{"role": "user", "content": content}],
        **extra,
    })
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def test_health():
    assert requests.get(f"{BASE}/health", timeout=10).json().get("status") is True


def test_model_available(auth):
    models = requests.get(f"{BASE}/api/models", headers=auth, timeout=30).json()["data"]
    assert MODEL in [m["id"] for m in models]


def test_chat(auth):
    assert chat(auth, "Reply with the single word: pong /no_think").strip()


def test_rag_answers_from_uploaded_document(auth):
    files = {"file": ("vault.txt", f"Internal memo.\n{SECRET_FACT}\n", "text/plain")}
    r = requests.post(f"{BASE}/api/v1/files/", headers=auth, files=files, timeout=120)
    r.raise_for_status()
    file_id = r.json()["id"]

    deadline = time.time() + 300
    status = "pending"
    while time.time() < deadline:
        status = requests.get(f"{BASE}/api/v1/files/{file_id}/process/status",
                              headers=auth, timeout=30).json().get("status")
        if status in ("completed", "failed"):
            break
        time.sleep(2)
    assert status == "completed", f"file processing ended with status={status}"

    answer = chat(auth, "What is the ORGOS vault access code? Answer with the code only. /no_think",
                  files=[{"type": "file", "id": file_id}])
    assert "ZEBRA-7731" in answer, answer
