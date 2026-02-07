import json
import os
import time
import random
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

_DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

# Use absolute path for ChromaDB to avoid conflicts
_CHROMA_BASE_DIR = Path(__file__).parent.parent.parent / ".chroma_db"
_CHROMA_BASE_DIR.mkdir(exist_ok=True)

# Check if we're in dry_run mode
_DRY_RUN = os.getenv("TRADING_MODE", "dry_run").lower() != "live"


class LocalEmbeddings(Embeddings):
    """Local embedding model using sentence-transformers with MPS (Apple GPU) acceleration."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Skip model loading in dry_run mode
        if _DRY_RUN:
            print("[DRY RUN] Skipping embedding model load (using fake embeddings)")
            self._model = None
        else:
            self._model = SentenceTransformer(model_name, device=_DEVICE)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if _DRY_RUN:
            # Return fake embeddings - just random vectors
            return [[random.random() for _ in range(384)] for _ in texts]
        return self._model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        if _DRY_RUN:
            # Return fake embedding
            return [random.random() for _ in range(384)]
        return self._model.encode([text], convert_to_numpy=True)[0].tolist()


from agents.polymarket.gamma import GammaMarketClient
from agents.utils.objects import SimpleEvent, SimpleMarket


class PolymarketRAG:
    def __init__(self, local_db_directory=None, embedding_function=None) -> None:
        self.gamma_client = GammaMarketClient()
        self.local_db_directory = local_db_directory
        self.embedding_function = embedding_function
        self.dry_run = _DRY_RUN
        
        if self.dry_run:
            print("[DRY RUN] RAG initialized - using fast mode (no model loading, fake embeddings)")

    def load_json_from_local(
        self, json_file_path=None, vector_db_directory="./local_db"
    ) -> None:
        loader = JSONLoader(
            file_path=json_file_path, jq_schema=".[].description", text_content=False
        )
        try:
            loaded_docs = list(loader.load())  # Convert generator to list to avoid StopIteration
        except StopIteration:
            loaded_docs = []

        embedding_function = LocalEmbeddings()
        Chroma.from_documents(
            loaded_docs, embedding_function, persist_directory=vector_db_directory
        )

    def create_local_markets_rag(self, local_directory="./local_db") -> None:
        all_markets = self.gamma_client.get_all_current_markets()

        if not os.path.isdir(local_directory):
            os.mkdir(local_directory)

        local_file_path = f"{local_directory}/all-current-markets_{time.time()}.json"

        with open(local_file_path, "w+") as output_file:
            json.dump(all_markets, output_file)

        self.load_json_from_local(
            json_file_path=local_file_path, vector_db_directory=local_directory
        )

    def query_local_markets_rag(
        self, local_directory=None, query=None
    ) -> "list[tuple]":
        embedding_function = LocalEmbeddings()
        local_db = Chroma(
            persist_directory=local_directory, embedding_function=embedding_function
        )
        response_docs = local_db.similarity_search_with_score(query=query)
        return response_docs

    def events(self, events: "list[SimpleEvent]", prompt: str) -> "list[tuple]":
        # Handle empty events list
        if not events or len(events) == 0:
            print("[WARNING] No events provided, returning empty results")
            return []
        
        # In dry_run mode, use super fast fake matching
        if self.dry_run:
            print(f"[DRY RUN] Fast mode: fake matching for {len(events)} events (no embeddings)")
            # Simple random selection with keyword bonus
            results = []
            prompt_lower = prompt.lower()
            
            for event in events[:10]:  # Consider first 10
                desc_lower = event.description.lower()
                # Give small bonus for keyword matches, otherwise random
                keyword_bonus = sum(1 for word in prompt_lower.split() if word in desc_lower)
                score = random.uniform(0.5, 1.0) - (keyword_bonus * 0.05)
                
                doc = Document(
                    page_content=event.description,
                    metadata={
                        "id": event.id,
                        "markets": event.markets
                    }
                )
                results.append((doc, score))
            
            # Sort by score (lower is better) and return top 5
            results.sort(key=lambda x: x[1])
            return results[:5] if results else [(Document(page_content=""), 1.0)]
        
        # Full embedding search for production
        local_events_directory = _CHROMA_BASE_DIR / "events"
        local_events_directory.mkdir(exist_ok=True)
        
        local_file_path = local_events_directory / "events.json"
        dict_events = [x.dict() for x in events]
        
        # Handle empty events list
        if not dict_events:
            print("[WARNING] No events to process, returning empty results")
            return []
        
        with open(local_file_path, "w+") as output_file:
            json.dump(dict_events, output_file)

        def metadata_func(record: dict, metadata: dict) -> dict:
            metadata["id"] = record.get("id")
            metadata["markets"] = record.get("markets")
            return metadata

        loader = JSONLoader(
            file_path=str(local_file_path),
            jq_schema=".[]",
            content_key="description",
            text_content=False,
            metadata_func=metadata_func,
        )
        try:
            # Convert generator to list to avoid StopIteration in Python 3.7+
            loaded_docs = []
            for doc in loader.load():
                loaded_docs.append(doc)
        except (StopIteration, RuntimeError) as e:
            # StopIteration is converted to RuntimeError in Python 3.7+
            if "StopIteration" in str(e) or isinstance(e, StopIteration):
                print("[WARNING] StopIteration caught, returning empty results")
            loaded_docs = []
        except Exception as e:
            print(f"[ERROR] Failed to load documents: {e}")
            loaded_docs = []
        
        if not loaded_docs:
            print("[WARNING] No documents loaded, returning empty results")
            return []
        
        embedding_function = LocalEmbeddings()
        vector_db_directory = local_events_directory / "chroma"
        local_db = Chroma.from_documents(
            loaded_docs, embedding_function, persist_directory=str(vector_db_directory)
        )

        return local_db.similarity_search_with_score(query=prompt)

    def markets(self, markets: "list[SimpleMarket]", prompt: str) -> "list[tuple]":
        # In dry_run mode, use super fast fake matching
        if self.dry_run:
            print(f"[DRY RUN] Fast mode: fake matching for {len(markets)} markets (no embeddings)")
            # Simple random selection with keyword bonus
            results = []
            prompt_lower = prompt.lower()
            
            for market in markets[:10]:  # Consider first 10
                desc = getattr(market, 'description', market.get('question', '')) if hasattr(market, 'description') else str(market.get('question', ''))
                desc_lower = str(desc).lower()
                # Give small bonus for keyword matches, otherwise random
                keyword_bonus = sum(1 for word in prompt_lower.split() if word in desc_lower)
                score = random.uniform(0.5, 1.0) - (keyword_bonus * 0.05)
                
                doc = Document(
                    page_content=desc,
                    metadata={
                        "id": market.get("id") if isinstance(market, dict) else market.id,
                        "outcomes": market.get("outcomes") if isinstance(market, dict) else market.outcomes,
                        "outcome_prices": market.get("outcome_prices") if isinstance(market, dict) else market.outcome_prices,
                        "question": market.get("question") if isinstance(market, dict) else market.question,
                        "clob_token_ids": market.get("clob_token_ids") if isinstance(market, dict) else getattr(market, 'clob_token_ids', None),
                    }
                )
                results.append((doc, score))
            
            # Sort by score (lower is better) and return top 5
            results.sort(key=lambda x: x[1])
            return results[:5] if results else [(Document(page_content=""), 1.0)]
        
        # Full embedding search for production
        local_markets_directory = _CHROMA_BASE_DIR / "markets"
        local_markets_directory.mkdir(exist_ok=True)
        
        local_file_path = local_markets_directory / "markets.json"
        
        # Handle empty markets list
        if not markets:
            print("[WARNING] No markets to process, returning empty results")
            return []
        
        with open(local_file_path, "w+") as output_file:
            json.dump(markets, output_file)

        def metadata_func(record: dict, metadata: dict) -> dict:
            metadata["id"] = record.get("id")
            metadata["outcomes"] = record.get("outcomes")
            metadata["outcome_prices"] = record.get("outcome_prices")
            metadata["question"] = record.get("question")
            metadata["clob_token_ids"] = record.get("clob_token_ids")
            return metadata

        loader = JSONLoader(
            file_path=str(local_file_path),
            jq_schema=".[]",
            content_key="description",
            text_content=False,
            metadata_func=metadata_func,
        )
        try:
            # Convert generator to list to avoid StopIteration in Python 3.7+
            loaded_docs = []
            for doc in loader.load():
                loaded_docs.append(doc)
        except (StopIteration, RuntimeError) as e:
            # StopIteration is converted to RuntimeError in Python 3.7+
            if "StopIteration" in str(e) or isinstance(e, StopIteration):
                print("[WARNING] StopIteration caught, returning empty results")
            loaded_docs = []
        except Exception as e:
            print(f"[ERROR] Failed to load documents: {e}")
            loaded_docs = []
        
        if not loaded_docs:
            print("[WARNING] No documents loaded, returning empty results")
            return []
        
        embedding_function = LocalEmbeddings()
        vector_db_directory = local_markets_directory / "chroma"
        local_db = Chroma.from_documents(
            loaded_docs, embedding_function, persist_directory=str(vector_db_directory)
        )

        return local_db.similarity_search_with_score(query=prompt)
