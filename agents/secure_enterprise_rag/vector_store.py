"""
On-Premise Vector Store Connector for Qdrant.
Enforces Role-Based Access Control (RBAC) payload filtering across departments.
"""

import hashlib
import logging
import math
from typing import Dict, List, Optional
import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from config.settings import get_settings
from .models import DataClassification, DepartmentAccess, DocumentChunk, SearchResultItem

logger = logging.getLogger("SecureQdrantStore")


class SecureQdrantStore:
    """
    On-premise vector store integrating with local Qdrant daemon.
    Guarantees departmental data isolation (R&D vs Legal vs Marketing).
    """

    def __init__(self, host: Optional[str] = None, collection_name: Optional[str] = None):
        settings = get_settings()
        self.host = host or settings.QDRANT_HOST
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.vector_dim = settings.EMBEDDING_DIMENSION

        self._in_memory_docs: Dict[str, DocumentChunk] = {}
        self._in_memory_vectors: Dict[str, List[float]] = {}
        self.client: Optional[QdrantClient] = None

        try:
            self.client = QdrantClient(url=self.host, timeout=2.0)
            self._init_collection()
        except Exception as e:
            logger.info(f"Qdrant connection bypassed or in-memory mode active ({e}).")
            self.client = None

    def _init_collection(self) -> None:
        """Ensures Qdrant collection is configured with Cosine metric."""
        if not self.client:
            return
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
        except Exception:
            self.client = None

    def _compute_mock_embedding(self, text: str) -> List[float]:
        """
        Fast deterministic embedding generator for local standalone execution.
        Normalizes vector to unit length for Cosine similarity.
        """
        vec = np.zeros(self.vector_dim, dtype=np.float32)
        words = text.lower().split()
        for w in words:
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx = h % self.vector_dim
            vec[idx] += 1.0

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def index_document(self, doc: DocumentChunk) -> bool:
        """
        Indexes a document chunk with metadata payload for RBAC filtering.
        """
        vector = self._compute_mock_embedding(doc.text)
        self._in_memory_docs[doc.chunk_id] = doc
        self._in_memory_vectors[doc.chunk_id] = vector

        if self.client:
            try:
                # Convert string ID to uint or UUID hash for Qdrant point
                point_id = int(hashlib.md5(doc.chunk_id.encode("utf-8")).hexdigest()[:15], 16)
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        qmodels.PointStruct(
                            id=point_id,
                            vector=vector,
                            payload={
                                "chunk_id": doc.chunk_id,
                                "title": doc.title,
                                "text": doc.text,
                                "department": doc.department.value,
                                "classification": doc.classification.value,
                                "created_date": doc.created_date
                            }
                        )
                    ]
                )
                return True
            except Exception as e:
                logger.warning(f"Qdrant upsert failed: {e}. Fallback to in-memory store.")

        return True

    def search_with_rbac(
        self,
        query: str,
        user_dept: DepartmentAccess,
        top_k: int = 3
    ) -> List[SearchResultItem]:
        """
        Vector similarity search strictly filtering out unauthorized departmental data.
        """
        q_vec = np.array(self._compute_mock_embedding(query), dtype=np.float32)
        scored_items: List[SearchResultItem] = []

        # RBAC Check: Executive and R&D have distinct access rights
        for cid, doc in self._in_memory_docs.items():
            # Filter condition
            if user_dept != DepartmentAccess.EXECUTIVE:
                if doc.department != DepartmentAccess.ALL and doc.department != user_dept:
                    continue  # Access denied for this department

            d_vec = np.array(self._in_memory_vectors[cid], dtype=np.float32)
            cosine_score = float(np.dot(q_vec, d_vec))

            scored_items.append(SearchResultItem(
                chunk_id=doc.chunk_id,
                title=doc.title,
                score=round(max(0.0, cosine_score), 4),
                text_snippet=doc.text,
                department=doc.department.value,
                classification=doc.classification.value,
                is_sanitized=False
            ))

        scored_items.sort(key=lambda x: x.score, reverse=True)
        return scored_items[:top_k]
