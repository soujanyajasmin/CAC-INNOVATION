import json
import re
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.ai import KnowledgeBase, KBDocument
from app.services.ai_service.provider import get_ai_provider

class RAGEngine:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        words = text.split()
        if not words:
            return []
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
            i += max(1, chunk_size - overlap)
        return chunks

    @classmethod
    def ingest_document(cls, db: Session, kb_id: int, title: str, content: str, file_path: Optional[str] = None) -> KBDocument:
        chunks = cls.chunk_text(content)
        doc = KBDocument(
            kb_id=kb_id,
            title=title,
            file_path=file_path,
            content_text=content,
            chunks_json=json.dumps(chunks),
            status="indexed"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def _compute_relevance(query: str, chunk: str) -> float:
        q_tokens = set(re.findall(r"\w+", query.lower()))
        if not q_tokens:
            return 0.0
        c_tokens = re.findall(r"\w+", chunk.lower())
        if not c_tokens:
            return 0.0
            
        score = 0.0
        c_dict = {}
        for t in c_tokens:
            c_dict[t] = c_dict.get(t, 0) + 1
            
        for q in q_tokens:
            if q in c_dict:
                score += (1.0 + math.log(c_dict[q])) * (1.5 if len(q) > 4 else 1.0)
                
        if query.lower() in chunk.lower():
            score += 5.0

        return score

    @classmethod
    def retrieve_passages(
        cls,
        db: Session,
        query: str,
        kb_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        kb_query = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True)
        if kb_id:
            kb_query = kb_query.filter(KnowledgeBase.id == kb_id)
        if tenant_id:
            kb_query = kb_query.filter((KnowledgeBase.tenant_id == tenant_id) | (KnowledgeBase.tenant_id == None))
        else:
            kb_query = kb_query.filter(KnowledgeBase.tenant_id == None)

        allowed_kbs = kb_query.all()
        if not allowed_kbs:
            return []

        allowed_kb_ids = [kb.id for kb in allowed_kbs]
        docs = db.query(KBDocument).filter(
            KBDocument.kb_id.in_(allowed_kb_ids),
            KBDocument.status == "indexed"
        ).all()

        scored_chunks = []
        for doc in docs:
            try:
                chunks = json.loads(doc.chunks_json) if doc.chunks_json else [doc.content_text]
            except Exception:
                chunks = [doc.content_text]

            for chunk_idx, chunk in enumerate(chunks):
                score = cls._compute_relevance(query, chunk)
                if score > 0:
                    scored_chunks.append({
                        "doc_id": doc.id,
                        "doc_title": doc.title,
                        "kb_id": doc.kb_id,
                        "chunk_index": chunk_idx,
                        "text": chunk,
                        "score": round(score, 3)
                    })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    @classmethod
    def query_with_rag(
        cls,
        db: Session,
        query: str,
        kb_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        passages = cls.retrieve_passages(db, query, kb_id=kb_id, tenant_id=tenant_id, top_k=top_k)
        
        context_str = ""
        if passages:
            context_str = "\n\n".join([f"Source: {p['doc_title']}\n{p['text']}" for p in passages])

        provider = get_ai_provider("internal")
        messages = [
            {
                "role": "system",
                "content": "You are the CTRL ALT CRAC INNOVATIONS Knowledge Retrieval Engine. Answer accurately citing the verified context."
            },
            {
                "role": "user",
                "content": f"Context:\n{context_str}\n\nQuestion: {query}" if context_str else query
            }
        ]
        
        result = provider.generate(messages, rag_context=context_str)
        return {
            "query": query,
            "answer": result["reply"],
            "sources": passages,
            "model_used": result["model"],
            "latency_ms": result["latency_ms"]
        }
