"""
主应用测试
"""
import pytest
from fastapi import status

@pytest.mark.unit
def test_root_endpoint(client):
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "message" in response.json()

@pytest.mark.unit
def test_api_docs(client):
    """测试API文档端点"""
    response = client.get("/docs")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.unit
def test_openapi_json(client):
    """测试OpenAPI JSON端点"""
    response = client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    assert "openapi" in response.json()
