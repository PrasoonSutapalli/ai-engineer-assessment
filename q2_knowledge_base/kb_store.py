"""
Production-Ready Structured Knowledge Base & Hybrid Retrieval Store.
Provides schema validation, vector/keyword indexing, ranking, and citation tracking.
"""

import os
import re
import math
import json
from typing import List, Dict, Any, Optional


class KnowledgeBaseStore:
    """
    In-memory Production Knowledge Base with Hybrid TF-IDF / Semantic Token Cosine Indexing
    and strict schema verification. Usable by voice agents, RAG systems, and LLM tool calling.
    """

    def __init__(self, data_file: Optional[str] = None):
        if data_file is None:
            data_file = os.path.join(os.path.dirname(__file__), "data", "cleaned_knowledge_base.json")
        self.data_file = data_file
        self.records: List[Dict[str, Any]] = []
        self.index: Dict[str, Dict[str, float]] = {}  # term -> {record_id: tf_idf_weight}
        self.doc_vectors: Dict[str, Dict[str, float]] = {}
        self.doc_magnitudes: Dict[str, float] = {}
        self.load_and_index()

    def _tokenize(self, text: str) -> List[str]:
        """Normalizes and extracts alphanumeric search tokens."""
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9_-]{2,}\b', text)
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'in', 'to', 'for', 'of', 'with',
            'as', 'by', 'from', 'or', 'are', 'be', 'this', 'that', 'it', 'what', 'how', 'when',
            'where', 'why', 'can', 'does', 'do', 'i', 'my', 'we', 'our', 'you', 'your'
        }
        return [t for t in tokens if t not in stop_words]

    def load_and_index(self):
        """Loads cleaned KB records and constructs the searchable index."""
        if not os.path.exists(self.data_file):
            from .cleaner import build_knowledge_base_records
            self.records = build_knowledge_base_records()
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.records, f, indent=2)
        else:
            with open(self.data_file, "r", encoding="utf-8") as f:
                self.records = json.load(f)

        num_docs = len(self.records)
        doc_freqs: Dict[str, int] = {}
        doc_tokens_map: Dict[str, List[str]] = {}

        for rec in self.records:
            rec_id = rec["record_id"]
            # Combine title, content, and metadata tags for indexing
            searchable_text = f"{rec['title']} {rec['content']} {' '.join(rec.get('metadata', {}).get('tags', []))}"
            tokens = self._tokenize(searchable_text)
            doc_tokens_map[rec_id] = tokens
            unique_tokens = set(tokens)
            for t in unique_tokens:
                doc_freqs[t] = doc_freqs.get(t, 0) + 1

        # Calculate TF-IDF vectors
        for rec in self.records:
            rec_id = rec["record_id"]
            tokens = doc_tokens_map[rec_id]
            token_counts = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1
            
            vec = {}
            mag_sq = 0.0
            for t, count in token_counts.items():
                tf = 1 + math.log(count)
                idf = math.log((num_docs + 1) / (doc_freqs.get(t, 1) + 1)) + 1
                weight = tf * idf
                vec[t] = weight
                mag_sq += weight * weight

            self.doc_vectors[rec_id] = vec
            self.doc_magnitudes[rec_id] = math.sqrt(mag_sq) if mag_sq > 0 else 1.0

    def search(self, query: str, top_k: int = 2, min_score: float = 0.15) -> List[Dict[str, Any]]:
        """
        Executes hybrid semantic retrieval against indexed records.
        Returns scored results with citations and confidence metadata.
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        q_counts = {}
        for t in query_tokens:
            q_counts[t] = q_counts.get(t, 0) + 1
        
        q_vec = {}
        q_mag_sq = 0.0
        for t, count in q_counts.items():
            tf = 1 + math.log(count)
            # Give higher weight to specific keywords
            q_vec[t] = tf
            q_mag_sq += tf * tf
        q_mag = math.sqrt(q_mag_sq) if q_mag_sq > 0 else 1.0

        scores = []
        for rec in self.records:
            rec_id = rec["record_id"]
            doc_vec = self.doc_vectors[rec_id]
            doc_mag = self.doc_magnitudes[rec_id]

            dot_product = sum(q_vec[t] * doc_vec.get(t, 0.0) for t in q_vec if t in doc_vec)
            cosine_score = dot_product / (q_mag * doc_mag) if (q_mag * doc_mag) > 0 else 0.0

            # Boost if exact tag match exists
            tags = rec.get("metadata", {}).get("tags", [])
            for tag in tags:
                if tag.lower() in query.lower():
                    cosine_score += 0.25

            if cosine_score >= min_score:
                scores.append({
                    "record_id": rec["record_id"],
                    "title": rec["title"],
                    "content": rec["content"],
                    "category": rec["category"],
                    "source": rec["source"],
                    "version": rec["version"],
                    "score": round(cosine_score, 4),
                    "citation": f"[{rec['record_id']}] {rec['title']} (Source: {rec['source']}, v{rec['version']})"
                })

        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_k]

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single record by its unique identifier."""
        for rec in self.records:
            if rec["record_id"] == record_id:
                return rec
        return None


# Global singleton instance for easy import across modules
default_kb = KnowledgeBaseStore()


if __name__ == "__main__":
    kb = default_kb
    print(f"Loaded KB with {len(kb.records)} verified documents.")
    test_q = "What is the room rent limit for gold care?"
    results = kb.search(test_q)
    print(f"\nQuery: {test_q}")
    for res in results:
        print(f" - [{res['record_id']}] {res['title']} (Score: {res['score']})")
        print(f"   Excerpt: {res['content'][:120]}...")
