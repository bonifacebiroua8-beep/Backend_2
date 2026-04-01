# app/services/chromadb_service.py
# FIX : ChromaDB entièrement optionnel — toutes les méthodes
#        retournent des valeurs par défaut si ChromaDB non disponible
import os
from typing import Optional, List
from loguru import logger

CHROMA_PATH = os.environ.get("CHROMA_PATH", "/tmp/ubuntutech_chroma")
_client     = None
_collection = None
_CHROMA_OK  = False


def _get_collection():
    global _client, _collection, _CHROMA_OK
    if _collection is not None:
        return _collection
    try:
        import chromadb
        from chromadb.config import Settings
        
        _client = chromadb.EphemeralClient(
            settings=Settings(anonymized_telemetry=False)
        )
        _collection = _client.get_or_create_collection(
            name="ubuntutech_apprentissages",
            metadata={"hnsw:space": "cosine"}
        )
        _CHROMA_OK = True
        logger.info(f"ChromaDB initialisé — {_collection.count()} entrées")
        return _collection
    except Exception as e:
        _CHROMA_OK = False
        logger.warning(f"ChromaDB non disponible (non bloquant) : {e}")
        return None


class ChromaDBService:

    @staticmethod
    def ajouter(texte_source: str, texte_traduit: str, langue: str,
                type_entree: str = "vocabulaire", contexte: str = "general",
                id_source: Optional[int] = None) -> bool:
        col = _get_collection()
        if col is None:
            return False
        try:
            import hashlib
            entrees = [
                {"id": f"src_{hashlib.md5(texte_source.encode()).hexdigest()[:12]}",
                 "texte": texte_source,
                 "meta": {"langue": langue, "type": type_entree, "signification": texte_traduit, "contexte": contexte}},
                {"id": f"trad_{hashlib.md5(texte_traduit.encode()).hexdigest()[:12]}",
                 "texte": texte_traduit,
                 "meta": {"langue": langue, "type": type_entree, "signification": texte_source, "contexte": contexte}},
                {"id": f"pair_{hashlib.md5((texte_source+texte_traduit).encode()).hexdigest()[:12]}",
                 "texte": f"{texte_source} = {texte_traduit}",
                 "meta": {"langue": langue, "type": "paire", "signification": f"{texte_source} → {texte_traduit}", "contexte": contexte}},
            ]
            for e in entrees:
                try:
                    col.upsert(ids=[e["id"]], documents=[e["texte"]], metadatas=[e["meta"]])
                except Exception:
                    pass
            return True
        except Exception as e:
            logger.error(f"ChromaDB ajouter : {e}")
            return False

    @staticmethod
    def rechercher(question: str, langue: Optional[str] = None, top_k: int = 8) -> List[dict]:
        col = _get_collection()
        if col is None:
            return []
        try:
            count = col.count()
            if count == 0:
                return []
            where  = {"langue": langue} if langue and langue != "fr" else None
            kwargs = {"query_texts": [question], "n_results": min(top_k, count)}
            if where:
                kwargs["where"] = where
            results = col.query(**kwargs)
            if not results or not results.get("documents"):
                return []
            items = []
            for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
                if dist < 0.85:
                    items.append({
                        "texte": doc, "signification": meta.get("signification", ""),
                        "langue": meta.get("langue", "fr"), "type": meta.get("type", "vocabulaire"),
                        "score": round(1 - dist, 3),
                    })
            return sorted(items, key=lambda x: x["score"], reverse=True)
        except Exception as e:
            logger.error(f"ChromaDB rechercher : {e}")
            return []

    @staticmethod
    def construire_contexte_rag(question: str, langue: str) -> str:
        try:
            resultats = ChromaDBService.rechercher(question, langue=langue, top_k=8)
            if not resultats:
                resultats = ChromaDBService.rechercher(question, top_k=5)
            if not resultats:
                return ""
            lignes = []
            vus = set()
            for r in resultats:
                sig = r.get("signification", "")
                txt = r.get("texte", "")
                cle = f"{txt}|{sig}"
                if cle not in vus and sig:
                    vus.add(cle)
                    lignes.append(f"• {txt} → {sig}")
            if not lignes:
                return ""
            return f"\n\n[Mémoire locale validée — langue {langue.upper()}]\n" + "\n".join(lignes[:6]) + "\n[Utilise ces informations pour répondre avec précision]\n"
        except Exception:
            return ""

    @staticmethod
    def stats() -> dict:
        col = _get_collection()
        if col is None:
            return {"total": 0, "par_langue": {}, "disponible": False}
        try:
            total = col.count()
            par_langue = {}
            for l in ["fr", "ff", "ha", "mfa", "en"]:
                try:
                    r = col.get(where={"langue": l})
                    par_langue[l] = len(r["ids"]) if r else 0
                except Exception:
                    par_langue[l] = 0
            return {"total": total, "par_langue": par_langue, "disponible": True}
        except Exception as e:
            logger.error(f"ChromaDB stats : {e}")
            return {"total": 0, "par_langue": {}, "disponible": False}

    @staticmethod
    def supprimer(texte: str) -> bool:
        col = _get_collection()
        if col is None:
            return False
        try:
            import hashlib
            col.delete(ids=[
                f"src_{hashlib.md5(texte.encode()).hexdigest()[:12]}",
                f"trad_{hashlib.md5(texte.encode()).hexdigest()[:12]}",
            ])
            return True
        except Exception as e:
            logger.error(f"ChromaDB supprimer : {e}")
            return False

    @staticmethod
    def lister(langue: Optional[str] = None, limit: int = 100) -> List[dict]:
        col = _get_collection()
        if col is None:
            return []
        try:
            kwargs = {"limit": limit}
            if langue:
                kwargs["where"] = {"langue": langue, "type": "paire"}
            r = col.get(**kwargs)
            if not r or not r.get("ids"):
                return []
            return [
                {"texte": doc, "signification": meta.get("signification", ""),
                 "langue": meta.get("langue", ""), "contexte": meta.get("contexte", "")}
                for doc, meta in zip(r["documents"], r["metadatas"])
                if meta.get("type") == "paire"
            ]
        except Exception as e:
            logger.error(f"ChromaDB lister : {e}")
            return []
