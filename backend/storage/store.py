"""
A tiny JSON-file-backed store for saved visualizations and projects.

This keeps the MVP dependency-free (no Postgres/Mongo to install for a
local demo). Swapping this for a real database later only requires
reimplementing this module's functions — nothing else in the app depends
on the storage format.
"""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "store")
os.makedirs(_DATA_DIR, exist_ok=True)
_EQUATIONS_FILE = os.path.join(_DATA_DIR, "equations.json")
_PROJECTS_FILE = os.path.join(_DATA_DIR, "projects.json")
_LOCK = threading.Lock()


def _read(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return []


def _write(path: str, data: List[Dict[str, Any]]) -> None:
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


def save_equation(payload: Dict[str, Any]) -> Dict[str, Any]:
    with _LOCK:
        items = _read(_EQUATIONS_FILE)
        record = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        items.insert(0, record)
        _write(_EQUATIONS_FILE, items)
        return record


def list_saved_equations(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = _read(_EQUATIONS_FILE)
    if project_id:
        items = [i for i in items if i.get("project_id") == project_id]
    return items


def delete_equation(equation_id: str) -> bool:
    with _LOCK:
        items = _read(_EQUATIONS_FILE)
        new_items = [i for i in items if i.get("id") != equation_id]
        changed = len(new_items) != len(items)
        if changed:
            _write(_EQUATIONS_FILE, new_items)
        return changed


def create_project(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    with _LOCK:
        items = _read(_PROJECTS_FILE)
        record = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        items.insert(0, record)
        _write(_PROJECTS_FILE, items)
        return record


def list_projects() -> List[Dict[str, Any]]:
    return _read(_PROJECTS_FILE)
