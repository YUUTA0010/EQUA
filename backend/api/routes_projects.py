from __future__ import annotations

from fastapi import APIRouter

from models.schemas import ProjectCreateRequest
from storage import store

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
def list_projects():
    return {"items": store.list_projects()}


@router.post("")
def create_project(req: ProjectCreateRequest):
    return store.create_project(req.name, req.description)
