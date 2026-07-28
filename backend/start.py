import sys
import os

print("=== STARTUP DEBUG ===", flush=True)
print(f"PORT={os.environ.get('PORT', 'NOT SET')}", flush=True)
print(f"ENABLE_TRACING={os.environ.get('ENABLE_TRACING', 'NOT SET')}", flush=True)
print(f"ENVIRONMENT={os.environ.get('ENVIRONMENT', 'NOT SET')}", flush=True)
print(f"CWD={os.getcwd()}", flush=True)

print("Step 1: importing app.main", flush=True)

from app.main import app

print("Step 2: app imported, starting uvicorn", flush=True)

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="debug")
