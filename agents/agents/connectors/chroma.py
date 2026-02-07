import json
import os
import time
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.embeddings import Embeddings

_DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

# Use absolute path for ChromaDB to avoid conflicts
_CHROMA_BASE_DIR = Path(__file__).parent.parent.parent / ".chroma_db"
_CHROMA_BASE_DIR.mkdir(exist_ok=True)


class LocalEmbeddings(Embeddings):
    """Local embedding model using sentence-transformers with MPS (Apple GPU) acceleration."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformer(model_name, device=_DEVICE)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode([text], convert_to_numpy=True)[0].tolist()


from agents.polymarket.gamma import GammaMarketClient
from agents.utils.objects import SimpleEvent, SimpleMarket


class PolymarketRAG:
    def __init__(self, local_db_directory=None, embedding_function=None) -> None:
        self.gamma_client = GammaMarketClient()
        self.local_db_directory = local_db_directory
        self.embedding_function = embedding_function
        self.dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
        
        if self.dry_run:
            print("[DRY RUN] RAG initialized - using lightweight embedding mode")

    def load_json_from_local(
        self, json_file_path=None, vector_db_directory="./local_db"
    ) -> None:
        loader = JSONLoader(
            file_path=json_file_path, jq_schema=".[].description", text_content=False
        )
        loaded_docs = loader.load()

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
        # In dry_run mode, skip embedding and return simple text match
        if self.dry_run and len(events) <= 20:
            print(f"[DRY RUN] Skipping embeddings, using simple text matching for {len(events)} events")
            # Simple keyword matching instead of vector search
            results = []
            prompt_lower = prompt.lower()
            for event in events[:5]:  # Return top 5 matches
                desc_lower = event.description.lower()
                # Simple scoring based on keyword overlap
                score = sum(word in desc_lower for word in prompt_lower.split())
                if score > 0:
                    # Mock Document object for compatibility
                    from langchain_core.documents import Document
                    doc = Document(
                        page_content=event.description,
                        metadata={
                            "id": event.id,
                            "markets": event.markets
                        }
                    )
                    results.append((doc, 1.0 - (score * 0.1)))  # Lower score is better
            return results if results else [(None, 1.0)]
        
        # Full embedding search for production or large datasets
        # create local json file with absolute path
        local_events_directory = _CHROMA_BASE_DIR / "events"
        local_events_directory.mkdir(exist_ok=True)
        
        local_file_path = local_events_directory / "events.json"
        dict_events = [x.dict() for x in events]
        with open(local_file_path, "w+") as output_file:
            json.dump(dict_events, output_file)

        # create vector db
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
        loaded_docs = loader.load()
        embedding_function = LocalEmbeddings()
        vector_db_directory = local_events_directory / "chroma"
        local_db = Chroma.from_documents(
            loaded_docs, embedding_function, persist_directory=str(vector_db_directory)
        )

        # query
        return local_db.similarity_search_with_score(query=prompt)

    def markets(self, markets: "list[SimpleMarket]", prompt: str) -> "list[tuple]":
        # In dry_run mode, skip embedding and return simple text match
        if self.dry_run and len(markets) <= 20:
            print(f"[DRY RUN] Skipping embeddings, using simple text matching for {len(markets)} markets")
            # Simple keyword matching instead of vector search
            results = []
            prompt_lower = prompt.lower()
            for market in markets[:5]:  # Return top 5 matches
                desc = getattr(market, 'description', market.get('question', ''))
                desc_lower = str(desc).lower()
                # Simple scoring based on keyword overlap
                score = sum(word in desc_lower for word in prompt_lower.split())
                if score > 0:
                    # Mock Document object for compatibility
                    from langchain_core.documents import Document
                    doc = Document(
                        page_content=desc,
                        metadata={
                            "id": market.get("id") if isinstance(market, dict) else market.id,
                            "outcomes": market.get("outcomes") if isinstance(market, dict) else market.outcomes,
                            "outcome_prices": market.get("outcome_prices") if isinstance(market, dict) else market.outcome_prices,
                            "question": market.get("question") if isinstance(market, dict) else market.question,
                            "clob_token_ids": market.get("clob_token_ids") if isinstance(market, dict) else market.clob_token_ids,
                        }
                    )
                    results.append((doc, 1.0 - (score * 0.1)))  # Lower score is better
            return results if results else [(None, 1.0)]
        
        # Full embedding search for production or large datasets
        # create local json file with absolute path
        local_markets_directory = _CHROMA_BASE_DIR / "markets"
        local_markets_directory.mkdir(exist_ok=True)
        
        local_file_path = local_markets_directory / "markets.json"
        with open(local_file_path, "w+") as output_file:
            json.dump(markets, output_file)

        # create vector db
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
        loaded_docs = loader.load()
        embedding_function = LocalEmbeddings()
        vector_db_directory = local_markets_directory / "chroma"
        local_db = Chroma.from_documents(
            loaded_docs, embedding_function, persist_directory=str(vector_db_directory)
        )

        # query
        return local_db.similarity_search_with_score(query=prompt)
