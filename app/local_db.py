"""
local_db.py — Lightweight JSON file-based database fallback.
Used when MongoDB Atlas is unreachable (e.g., cluster paused / no internet).
Stores users in carebridge_local.json inside the project root.
"""

import json
import os
import threading
from pathlib import Path
from datetime import datetime

DB_FILE = Path(__file__).parent / 'carebridge_local.json'

if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    TMP_FILE = Path('/tmp') / 'carebridge_local.json'
    if not TMP_FILE.exists() and DB_FILE.exists():
        try:
            import shutil
            shutil.copy(DB_FILE, TMP_FILE)
        except Exception as e:
            print(f"[WARNING] Failed to copy fallback DB to /tmp: {e}")
    DB_FILE = TMP_FILE

_lock = threading.Lock()


def _load() -> dict:
    if DB_FILE.exists():
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'users': []}



def _save(data: dict) -> None:
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


class _Collection:
    """Mimics a pymongo Collection for find_one / insert_one."""

    def __init__(self, name: str):
        self._name = name

    def find_one(self, query: dict) -> dict | None:
        with _lock:
            data = _load()
            records = data.get(self._name, [])
            for rec in records:
                if self._matches(rec, query):
                    return rec
            return None

    def find(self, query: dict = None) -> list:
        with _lock:
            data = _load()
            records = data.get(self._name, [])
            if not query:
                return list(records)
            return [r for r in records if self._matches(r, query)]

    def insert_one(self, doc: dict):
        with _lock:
            data = _load()
            records = data.setdefault(self._name, [])
            # Generate a simple unique ID
            import uuid
            doc = dict(doc)
            doc['_id'] = str(uuid.uuid4())
            doc['created_at'] = datetime.utcnow().isoformat()
            records.append(doc)
            _save(data)

            class Result:
                def __init__(self, inserted_id):
                    self.inserted_id = inserted_id
            return Result(doc['_id'])

    def update_one(self, query: dict, update: dict) -> None:
        with _lock:
            data = _load()
            records = data.get(self._name, [])
            for rec in records:
                if self._matches(rec, query):
                    if '$set' in update:
                        rec.update(update['$set'])
                    break
            _save(data)

    @staticmethod
    def _matches(record: dict, query: dict) -> bool:
        if not query:
            return True
        if '$or' in query:
            return any(
                _Collection._matches(record, sub)
                for sub in query['$or']
            )
        for key, value in query.items():
            if key.startswith('$'):
                continue
            if record.get(key) != value:
                return False
        return True


class _LocalDB:
    """Mimics the pymongo Database object."""
    def __getattr__(self, name: str) -> _Collection:
        return _Collection(name)


local_db = _LocalDB()
