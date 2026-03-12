from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, flows, forms, instances, inbox, users, audit, expressions

app = FastAPI(
    title="e-Flow Enterprise API",
    version="1.0.0",
    description="Enterprise BPM / Workflow Automation Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(flows.router)
app.include_router(forms.router)
app.include_router(instances.router)
app.include_router(inbox.router)
app.include_router(users.router)
app.include_router(audit.router)
app.include_router(expressions.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "e-Flow Enterprise API"}


@app.get("/")
async def root():
    return {"name": "e-Flow Enterprise", "version": "1.0.0", "docs": "/docs"}
