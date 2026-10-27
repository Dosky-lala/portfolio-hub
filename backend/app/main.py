from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Project
from .schemas import ProjectCreate, ProjectOut, ProjectUpdate

# One reusable type: "a database session, provided per request by get_db".
# Annotated puts Depends in the TYPE, not the default value (FastAPI's recommended style).
DbSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Chapter 1 shortcut: create tables on startup.
    # Known gap -> replaced by proper migrations (Kubernetes Job) in Chapter 2.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Portfolio Hub API",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)


@app.get("/api/health")
def health(response: Response, db: DbSession):
    """Healthy only if the database answers. 503 lets orchestrators detect 'alive but useless'."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", "db": "unreachable"}


def get_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


@app.get("/api/projects", response_model=list[ProjectOut])
def list_projects(db: DbSession):
    return db.scalars(select(Project).order_by(Project.chapter)).all()


@app.get("/api/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: DbSession):
    return get_or_404(db, project_id)


@app.post("/api/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: DbSession):
    project = Project(**payload.model_dump(mode="json"))  # mode="json": URLs -> plain strings
    db.add(project)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        # "from err" keeps the original database error attached for debugging
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Chapter {payload.chapter} already exists"
        ) from err
    db.refresh(project)
    return project


@app.patch("/api/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate, db: DbSession):
    project = get_or_404(db, project_id)
    changes = payload.model_dump(mode="json", exclude_unset=True)  # only fields actually sent
    gate_changes = changes.pop("gate", None)
    for field, value in changes.items():
        setattr(project, field, value)
    if gate_changes:
        # Assign a NEW dict: SQLAlchemy doesn't notice in-place edits to a JSON column,
        # so mutating project.gate directly would silently never save.
        project.gate = {**project.gate, **gate_changes}
    db.commit()
    db.refresh(project)
    return project


@app.delete("/api/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: DbSession):
    db.delete(get_or_404(db, project_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
