"""In-memory stand-ins for Supabase and Pinecone (no network in tests)."""

import uuid
from types import SimpleNamespace

from gotrue.errors import AuthApiError


class FakeResponse:
    def __init__(self, data: list[dict]) -> None:
        self.data = data


class FakeQuery:
    def __init__(self, db: "FakeSupabase", table: str) -> None:
        self._db = db
        self._table = table
        self._filters: list[tuple[str, object]] = []
        self._limit: int | None = None
        self._op = "select"
        self._payload: dict = {}

    def select(self, *_columns: str) -> "FakeQuery":
        return self

    def eq(self, column: str, value: object) -> "FakeQuery":
        self._filters.append((column, value))
        return self

    def limit(self, n: int) -> "FakeQuery":
        self._limit = n
        return self

    def insert(self, payload: dict) -> "FakeQuery":
        self._op, self._payload = "insert", payload
        return self

    def update(self, payload: dict) -> "FakeQuery":
        self._op, self._payload = "update", payload
        return self

    def execute(self) -> FakeResponse:
        rows = self._db.tables.setdefault(self._table, [])
        if self._op == "insert":
            row = {"id": str(uuid.uuid4()), **self._payload}
            rows.append(row)
            return FakeResponse([dict(row)])
        matched = [r for r in rows if all(r.get(c) == v for c, v in self._filters)]
        if self._op == "update":
            for row in matched:
                row.update(self._payload)
        return FakeResponse([dict(r) for r in matched[: self._limit]])


class FakeBucket:
    def __init__(self, name: str, files: dict[str, bytes]) -> None:
        self._name = name
        self._files = files

    def upload(self, key: str, contents: bytes, _options: dict | None = None) -> None:
        self._files[key] = contents

    def get_public_url(self, key: str) -> str:
        return f"https://storage.example.com/{self._name}/{key}"


class FakeStorage:
    def __init__(self) -> None:
        self.files: dict[str, dict[str, bytes]] = {}

    def from_(self, bucket: str) -> FakeBucket:
        return FakeBucket(bucket, self.files.setdefault(bucket, {}))


class FakeAuth:
    def __init__(self) -> None:
        self.tokens: dict[str, SimpleNamespace] = {}

    def add_user(self, token: str, user_id: str, email: str) -> None:
        self.tokens[token] = SimpleNamespace(id=user_id, email=email)

    def get_user(self, token: str) -> SimpleNamespace:
        if token not in self.tokens:
            raise AuthApiError("invalid JWT", 401, "bad_jwt")
        return SimpleNamespace(user=self.tokens[token])


class FakeSupabase:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict]] = {}
        self.storage = FakeStorage()
        self.auth = FakeAuth()

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self, name)

    from_ = table


class FakeIndex:
    def __init__(self) -> None:
        self.vectors: dict[str, tuple[list[float], dict]] = {}

    def upsert(self, vectors: list[tuple[str, list[float], dict]]) -> None:
        for vector_id, values, metadata in vectors:
            self.vectors[vector_id] = (values, metadata)
