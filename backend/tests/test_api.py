import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns expected response"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to Rocketlane Assist API"
    assert "version" in response.json()
    assert "docs" in response.json()


def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_config_get_without_keys():
    """Test getting config when no API keys are set"""
    response = client.get("/api/v1/config/")
    assert response.status_code == 200
    data = response.json()
    assert "llm_provider" in data
    assert "llm_model" in data
    assert "has_openai_key" in data
    assert "has_anthropic_key" in data
    assert "has_rocketlane_key" in data