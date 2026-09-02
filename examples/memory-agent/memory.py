"""Small, dependency-free memory stores used by the memory-agent example.

The interfaces deliberately mirror the operations an agent needs from a vector index
and a graph database.  A production deployment can replace ``VectorMemory`` with FAISS
and ``GraphMemory`` with NetworkX without changing session or decay policy.  Keeping
the example in the standard library makes it safe to run in CI and on an edge device.
"""

from __future__ import annotations

import math
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

try:  # Optional accelerators; the standard-library backend remains the default.
    import faiss
    import numpy as np
except ImportError:  # pragma: no cover - exercised only in minimal environments
    faiss = None
    np = None

try:
    import networkx as nx
except ImportError:  # pragma: no cover - exercised only in minimal environments
    nx = None


@dataclass(frozen=True)
class MemoryRecord:
    text: str
    embedding: tuple[float, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class VectorMemory:
    """An in-process vector memory with a FAISS-compatible ``add``/``search`` shape."""

    def __init__(self, embedding_dim: int = 384, use_faiss: bool = False) -> None:
        if embedding_dim <= 0:
            raise ValueError("embedding_dim must be positive")
        self.embedding_dim = embedding_dim
        self._records: list[MemoryRecord] = []
        if use_faiss and (faiss is None or np is None):
            raise RuntimeError("FAISS backend requires faiss-cpu and numpy")
        self._index = faiss.IndexFlatL2(embedding_dim) if use_faiss else None

    @property
    def size(self) -> int:
        return len(self._records)

    def add(
        self,
        text: str,
        embedding: Sequence[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        vector = tuple(float(value) for value in embedding)
        self._check_dimension(vector)
        self._records.append(MemoryRecord(text, vector, dict(metadata or {})))
        if self._index is not None:
            self._index.add(np.asarray(vector, dtype="float32").reshape(1, -1))

    def search(
        self, query_embedding: Sequence[float], k: int = 3
    ) -> list[dict[str, Any]]:
        if k <= 0:
            return []
        query = tuple(float(value) for value in query_embedding)
        self._check_dimension(query)
        if self._index is not None and self._records:
            distances, indices = self._index.search(
                np.asarray(query, dtype="float32").reshape(1, -1), min(k, len(self._records))
            )
            ranked = [
                (float(distance), self._records[int(index)])
                for distance, index in zip(distances[0], indices[0])
            ]
        else:
            ranked = sorted(
                ((self._distance(query, record.embedding), record) for record in self._records),
                key=lambda item: item[0],
            )
        return [
            {
                "text": record.text,
                "metadata": dict(record.metadata),
                "distance": distance,
                "created_at": record.created_at.isoformat(),
            }
            for distance, record in ranked[:k]
        ]

    def _check_dimension(self, vector: Sequence[float]) -> None:
        if len(vector) != self.embedding_dim:
            raise ValueError(
                f"embedding has dimension {len(vector)}; expected {self.embedding_dim}"
            )

    @staticmethod
    def _distance(left: Sequence[float], right: Sequence[float]) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


class GraphMemory:
    """A bounded directed relationship graph represented with standard-library sets."""

    def __init__(self, use_networkx: bool = False) -> None:
        if use_networkx and nx is None:
            raise RuntimeError("NetworkX backend requires networkx")
        self._edges: dict[str, dict[str, set[str]]] = {}
        self._graph = nx.MultiDiGraph() if use_networkx else None

    def add_relationship(self, source: str, relation: str, target: str) -> None:
        self._edges.setdefault(source, {}).setdefault(relation, set()).add(target)
        if self._graph is not None:
            self._graph.add_edge(source, target, relation=relation)

    def related(self, source: str, relation: str | None = None) -> set[str]:
        relationships = self._edges.get(source, {})
        if relation is None:
            return {target for targets in relationships.values() for target in targets}
        return set(relationships.get(relation, set()))

    def relationships(self, source: str) -> dict[str, set[str]]:
        return {relation: set(targets) for relation, targets in self._edges.get(source, {}).items()}


class TimeDecayMemory:
    """Key/value memory whose relevance decays exponentially after ``half_life`` seconds."""

    def __init__(
        self,
        half_life: float = 86_400.0,
        clock: Callable[[], float] = time.time,
        decay_rate: float | None = None,
    ) -> None:
        if decay_rate is not None:
            if decay_rate <= 0:
                raise ValueError("decay_rate must be positive")
            half_life = math.log(2) / decay_rate
        if half_life <= 0:
            raise ValueError("half_life must be positive")
        self.half_life = half_life
        self._clock = clock
        self._items: dict[str, tuple[str, float]] = {}

    def add(self, key: str, value: str) -> None:
        self._items[key] = (value, self._clock())

    def get(self, key: str) -> str | None:
        item = self._items.get(key)
        if item is None:
            return None
        value, created = item
        age = max(0.0, self._clock() - created)
        weight = math.pow(0.5, age / self.half_life)
        if weight < 0.1:
            self._items.pop(key, None)
            return None
        return value

    def weight(self, key: str) -> float:
        item = self._items.get(key)
        if item is None:
            return 0.0
        age = max(0.0, self._clock() - item[1])
        return math.pow(0.5, age / self.half_life)


class SessionMemory:
    """Session-scoped composition of vector, graph, and decaying memory."""

    def __init__(
        self, embedding_dim: int = 384, clock: Callable[[], float] = time.time
    ) -> None:
        self.vector = VectorMemory(embedding_dim)
        self.graph = GraphMemory()
        self.recent = TimeDecayMemory(clock=clock)
        self.session_id: str | None = None

    def start(self, session_id: str) -> None:
        if not session_id.strip():
            raise ValueError("session_id must not be empty")
        self.session_id = session_id

    def remember(
        self,
        text: str,
        embedding: Sequence[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self.session_id is None:
            raise RuntimeError("start a session before remembering")
        details = dict(metadata or {})
        details.setdefault("session_id", self.session_id)
        self.vector.add(text, embedding, details)
        self.recent.add(self.session_id, text)

    def recall(self, embedding: Sequence[float], k: int = 3) -> list[dict[str, Any]]:
        return self.vector.search(embedding, k)
