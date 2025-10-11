import os, uvicorn
from api.main import app  # <= força o PyInstaller a incluir o pacote 'api'

os.environ.setdefault("ENGINE_MODULE", "engine.local_test.pdf_ops")
os.environ.setdefault("ENGINE_LOCAL_LOG", "1")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "*")

if __name__ == "__main__":
    uvicorn.run(
        app,                       # <= passa o objeto, não a string
        host="127.0.0.1",
        port=8000,
        log_level="info",
        log_config=None,
        access_log=False
    )
