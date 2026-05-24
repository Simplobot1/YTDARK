from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch

client = TestClient(app)

def test_login_sucesso():
    with patch("app.routes.auth._get_users", return_value={"admin@test.com": "senha123"}):
        with patch("app.routes.auth.verify_password", return_value=True):
            resp = client.post("/auth/login", json={"email": "admin@test.com", "senha": "senha123"})
    assert resp.status_code == 200
    assert "token" in resp.json()

def test_login_credenciais_invalidas():
    with patch("app.routes.auth._get_users", return_value={"admin@test.com": "outrasenha"}):
        with patch("app.routes.auth.verify_password", return_value=False):
            resp = client.post("/auth/login", json={"email": "admin@test.com", "senha": "errada"})
    assert resp.status_code == 401

def test_health_sem_auth():
    resp = client.get("/health")
    assert resp.status_code == 200
