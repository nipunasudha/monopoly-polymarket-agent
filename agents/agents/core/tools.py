"""Tool registry for OpenClaw-inspired architecture.

Centralized tool definitions using Claude SDK format.
"""

import os
from typing import Dict, Callable, Any, List, Optional
from dotenv import load_dotenv

try:
    from exa_py import Exa
except ImportError:
    Exa = None

from tavily import TavilyClient

# Import existing clients
from agents.polymarket.gamma import GammaMarketClient
from agents.polymarket.polymarket import Polymarket

load_dotenv()


class ToolRegistry:
    """Centralized tool definitions using Claude SDK format.
    
    This registry manages tool schemas and executors for:
    - Exa search (high-quality web research)
    - Tavily search (general web search)
    - Polymarket API (market data, execution)
    - Memory store (insight persistence)
    """
    
    def __init__(self):
        """Initialize tool registry with API clients."""
        # Initialize Exa client if available
        exa_api_key = os.getenv("EXA_API_KEY")
        if Exa and exa_api_key:
            self.exa = Exa(api_key=exa_api_key)
        else:
            self.exa = None
            if not Exa:
                print("[WARNING] exa-py not installed. Exa tools will be unavailable.")
            elif not exa_api_key:
                print("[WARNING] EXA_API_KEY not set. Exa tools will be unavailable.")
        
        # Initialize Tavily client
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if tavily_api_key:
            self.tavily = TavilyClient(api_key=tavily_api_key)
        else:
            self.tavily = None
            print("[WARNING] TAVILY_API_KEY not set. Tavily tools will be unavailable.")
        
        # Initialize Polymarket clients
        self.gamma = GammaMarketClient()
        self.polymarket = Polymarket()
        
        # Tool storage
        self.tools: Dict[str, Dict] = {}
        self.executors: Dict[str, Callable] = {}
        
        # Register all default tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register Exa, Tavily, Polymarket tools with Claude SDK format schemas."""
        
        # Exa Research Tool
        if self.exa:
            self.register_tool(
                name="exa_research",
                description="High-quality web research using Exa. Use this for deep research on specific topics, finding recent news, and getting authoritative sources.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Research query or topic to investigate"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        },
                        "use_autoprompt": {
                            "type": "boolean",
                            "description": "Whether to use Exa's autoprompt feature (default: True)",
                            "default": True
                        }
                    },
                    "required": ["query"]
                },
                executor=self._execute_exa_research
            )
        
        # Tavily Search Tool
        if self.tavily:
            self.register_tool(
                name="tavily_search",
                description="General web search using Tavily. Use this for quick searches and finding general information.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                },
                executor=self._execute_tavily_search
            )
        
        # Polymarket Market Data Tool
        self.register_tool(
            name="get_market_data",
            description="Get detailed market data from Polymarket including prices, liquidity, and outcomes.",
            input_schema={
                "type": "object",
                "properties": {
                    "market_id": {
                        "type": "string",
                        "description": "Market ID or token ID"
                    }
                },
                "required": ["market_id"]
            },
            executor=self._execute_get_market_data
        )
        
        # Polymarket Market List Tool
        self.register_tool(
            name="list_markets",
            description="List available markets from Polymarket with optional filtering.",
            input_schema={
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "Only return active markets (default: True)",
                        "default": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of markets to return (default: 20)",
                        "default": 20
                    },
                    "category_filter": {
                        "type": "string",
                        "description": "Optional category/keyword filter"
                    }
                },
                "required": []
            },
            executor=self._execute_list_markets
        )
        
        # Memory Store Tool (placeholder for future implementation)
        self.register_tool(
            name="store_insight",
            description="Store an insight or research finding for later retrieval. Useful for maintaining context across conversations.",
            input_schema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Unique key for the insight"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content of the insight to store"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata (market_id, timestamp, etc.)"
                    }
                },
                "required": ["key", "content"]
            },
            executor=self._execute_store_insight
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        executor: Callable
    ):
        """Register a new tool.
        
        Args:
            name: Tool name (must be unique)
            description: Tool description for LLM
            input_schema: JSON schema for tool inputs (Claude SDK format)
            executor: Callable that executes the tool
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema
        }
        self.executors[name] = executor
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas in Claude SDK format.
        
        Returns:
            List of tool schemas ready for Claude API
        """
        return list(self.tools.values())
    
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a registered tool.
        
        Args:
            name: Tool name
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        if name not in self.executors:
            raise ValueError(f"Tool '{name}' not found in registry")
        
        executor = self.executors[name]
        return await executor(**kwargs) if hasattr(executor, '__call__') else executor(**kwargs)
    
    # Tool executors
    
    async def _execute_exa_research(
        self,
        query: str,
        num_results: int = 5,
        use_autoprompt: bool = True
    ) -> Dict[str, Any]:
        """Execute Exa research query."""
        if not self.exa:
            return {
                "error": "Exa client not available. Set EXA_API_KEY environment variable."
            }
        
        try:
            results = self.exa.search(
                query=query,
                num_results=num_results,
                use_autoprompt=use_autoprompt
            )
            
            # Format results for Claude
            formatted_results = []
            for result in results.results:
                formatted_results.append({
                    "title": result.title,
                    "url": result.url,
                    "text": result.text,
                    "published_date": result.published_date,
                    "author": result.author
                })
            
            return {
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results)
            }
        except Exception as e:
            return {
                "error": f"Exa research failed: {str(e)}",
                "query": query
            }
    
    async def _execute_tavily_search(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Execute Tavily search query."""
        if not self.tavily:
            return {
                "error": "Tavily client not available. Set TAVILY_API_KEY environment variable."
            }
        
        try:
            # Use Tavily's search context method
            context = self.tavily.get_search_context(query=query, max_results=max_results)
            
            return {
                "query": query,
                "context": context,
                "max_results": max_results
            }
        except Exception as e:
            return {
                "error": f"Tavily search failed: {str(e)}",
                "query": query
            }
    
    async def _execute_get_market_data(self, market_id: str) -> Dict[str, Any]:
        """Get market data from Polymarket."""
        try:
            market = self.polymarket.get_market(market_id)
            
            return {
                "market_id": market_id,
                "question": market.question,
                "description": market.description,
                "active": market.active,
                "spread": market.spread,
                "outcomes": market.outcomes,
                "outcome_prices": market.outcome_prices,
                "end_date": market.end
            }
        except Exception as e:
            return {
                "error": f"Failed to get market data: {str(e)}",
                "market_id": market_id
            }
    
    async def _execute_list_markets(
        self,
        active_only: bool = True,
        limit: int = 20,
        category_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """List markets from Polymarket."""
        try:
            markets = self.polymarket.get_all_markets(
                active_only=active_only,
                category_filter=category_filter
            )
            
            # Limit results
            markets = markets[:limit]
            
            # Format for response
            formatted_markets = []
            for market in markets:
                formatted_markets.append({
                    "id": market.id,
                    "question": market.question,
                    "description": market.description,
                    "active": market.active,
                    "spread": market.spread,
                    "end_date": market.end
                })
            
            return {
                "markets": formatted_markets,
                "count": len(formatted_markets),
                "active_only": active_only,
                "category_filter": category_filter
            }
        except Exception as e:
            return {
                "error": f"Failed to list markets: {str(e)}"
            }
    
    async def _execute_store_insight(
        self,
        key: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store an insight (placeholder implementation).
        
        TODO: Integrate with actual memory store (e.g., ChromaDB or database)
        """
        # Placeholder - will be implemented in later phases
        return {
            "status": "stored",
            "key": key,
            "content": content[:100] + "..." if len(content) > 100 else content,
            "metadata": metadata or {}
        }
