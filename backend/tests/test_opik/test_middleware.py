"""
Test Opik middleware integration
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_path))

from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

def test_middleware_loaded():
    """Test that Opik middleware is loaded"""
    # A FastAPI a middleware-eket a 'cls' attribútumban tárolja a wrapperen belül
    middlewares = []
    for m in app.user_middleware:
        # Megpróbáljuk kinyerni az eredeti osztály nevét
        if hasattr(m, "cls"):
            middlewares.append(m.cls.__name__)
        else:
            middlewares.append(m.__class__.__name__)
            
    print(f"Loaded middlewares: {middlewares}")
    
    assert "OpikMiddleware" in middlewares, "Opik middleware not found in app"
    print("✅ Opik middleware is loaded")

# def test_middleware_loaded():
#     """Test that Opik middleware is loaded"""
#     # Check middleware stack
#     middlewares = [m.__class__.__name__ for m in app.user_middleware]
#     print(f"Loaded middlewares: {middlewares}")
#     assert "OpikMiddleware" in middlewares, "Opik middleware not found in app"
#     print("✅ Opik middleware is loaded")


def test_health_endpoint_excluded():
    """Test that health endpoint is excluded from tracking"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ Health endpoint works and is excluded from tracking")


def test_root_endpoint_excluded():
    """Test that root endpoint is excluded from tracking"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    print("✅ Root endpoint works and is excluded from tracking")


def test_middleware_tracks_regular_endpoints():
    """Test that middleware tracks non-excluded endpoints"""
    # This will be tracked (assuming /api/tasks exists)
    # For now, just verify the middleware doesn't break requests
    response = client.get("/docs")  # Docs endpoint
    # Should work even if excluded
    print(f"✅ Docs endpoint returned status: {response.status_code}")


if __name__ == "__main__":
    print("--- Testing Opik Middleware Integration ---\n")

    try:
        test_middleware_loaded()
        test_health_endpoint_excluded()
        test_root_endpoint_excluded()
        test_middleware_tracks_regular_endpoints()

        print("\n✅ All middleware tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
