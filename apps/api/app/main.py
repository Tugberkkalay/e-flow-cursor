from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import auth_router, flows_router, forms_router, instances_router, inbox_router, admin_router, expression_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="e-Flow Enterprise API",
    description="Enterprise BPM & Workflow Automation Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(flows_router.router)
app.include_router(forms_router.router)
app.include_router(instances_router.router)
app.include_router(inbox_router.router)
app.include_router(admin_router.router)
app.include_router(expression_router.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "e-Flow Enterprise"}
