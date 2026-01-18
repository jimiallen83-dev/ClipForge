from fastapi.testclient import TestClient
import app

client = TestClient(app.app)
print("calling /projects/1/timeline")
r = client.get("/projects/1/timeline")
print("status", r.status_code)
print("body", r.text)
