"""ResearchAgent - Specialized agent for market research."""

import hashlib
from typing import Dict, Any, Optional
from agents.core.hub import TradingHub
from agents.core.session import Lane, Task


class ResearchAgent:
    """Specialized agent for market research using Exa and Tavily.
    
    This agent performs deep research on markets by:
    - Using Exa for high-quality, authoritative sources
    - Using Tavily for general web search
    - Storing insights for later retrieval
    """
    
    def __init__(self, hub: TradingHub):
        """Initialize ResearchAgent.
        
        Args:
            hub: TradingHub instance for task execution
        """
        self.hub = hub
        self.system_prompt = """You are a research analyst specializing in prediction market research.

Your role is to gather comprehensive information about markets, events, and topics to inform trading decisions.

Guidelines:
- Use exa_research for deep, authoritative research on specific topics
- Use tavily_search for general web searches and current events
- Focus on recent news, trends, and factual information
- Store important insights using store_insight for later reference
- Provide clear, structured summaries of your findings
- Cite sources when possible
- Be objective and data-driven in your analysis

When researching a market:
1. Understand the market question and context
2. Search for recent news and developments
3. Identify key factors that could influence the outcome
4. Summarize findings clearly
5. Store important insights for future reference"""
    
    async def research_market(
        self,
        market_question: str,
        market_description: Optional[str] = None,
        session_id: Optional[str] = None,
        priority: int = 5
    ) -> str:
        """Perform deep research on a market.
        
        Args:
            market_question: The market question to research
            market_description: Optional market description for context
            session_id: Optional session ID for maintaining context
            priority: Task priority (higher = more important)
            
        Returns:
            Task ID (use hub.enqueue_and_wait() to get result)
        """
        # Generate unique task ID from market question
        task_id = f"research_{hashlib.md5(market_question.encode()).hexdigest()[:12]}"
        
        # Build research prompt
        prompt_parts = [
            f"Research this prediction market: {market_question}"
        ]
        
        if market_description:
            prompt_parts.append(f"\nMarket description: {market_description}")
        
        prompt_parts.extend([
            "\nPlease:",
            "1. Use exa_research to find recent, authoritative sources about this topic",
            "2. Use tavily_search to find current news and general information",
            "3. Analyze the information and identify key factors that could influence the outcome",
            "4. Provide a structured summary with:",
            "   - Key recent developments",
            "   - Important factors to consider",
            "   - Overall assessment",
            "5. Store important insights using store_insight for future reference"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Create task
        task = Task(
            id=task_id,
            lane=Lane.RESEARCH,
            prompt=prompt,
            tools=["exa_research", "tavily_search", "store_insight"],
            context={
                "market_question": market_question,
                "market_description": market_description,
                "agent_type": "research"
            },
            session_id=session_id,
            priority=priority
        )
        
        return await self.hub.enqueue(task)
    
    async def research_market_and_wait(
        self,
        market_question: str,
        market_description: Optional[str] = None,
        session_id: Optional[str] = None,
        timeout: Optional[float] = 300.0
    ) -> Dict[str, Any]:
        """Research market and wait for result.
        
        Args:
            market_question: The market question to research
            market_description: Optional market description for context
            session_id: Optional session ID for maintaining context
            timeout: Optional timeout in seconds
            
        Returns:
            Research result dictionary
        """
        # Generate unique task ID
        import hashlib
        task_id = f"research_{hashlib.md5(market_question.encode()).hexdigest()[:12]}"
        
        # Build research prompt
        prompt_parts = [
            f"Research this prediction market: {market_question}"
        ]
        
        if market_description:
            prompt_parts.append(f"\nMarket description: {market_description}")
        
        prompt_parts.extend([
            "\nPlease:",
            "1. Use exa_research to find recent, authoritative sources about this topic",
            "2. Use tavily_search to find current news and general information",
            "3. Analyze the information and identify key factors that could influence the outcome",
            "4. Provide a structured summary with:",
            "   - Key recent developments",
            "   - Important factors to consider",
            "   - Overall assessment",
            "5. Store important insights using store_insight for future reference"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Create and enqueue task, then wait for result
        task = Task(
            id=task_id,
            lane=Lane.RESEARCH,
            prompt=prompt,
            tools=["exa_research", "tavily_search", "store_insight"],
            context={
                "market_question": market_question,
                "market_description": market_description,
                "agent_type": "research"
            },
            session_id=session_id,
            priority=5
        )
        
        return await self.hub.enqueue_and_wait(task, timeout=timeout)
    
    async def quick_search(
        self,
        query: str,
        session_id: Optional[str] = None,
        priority: int = 3
    ) -> str:
        """Perform a quick search (uses Tavily only).
        
        Args:
            query: Search query
            session_id: Optional session ID
            priority: Task priority
            
        Returns:
            Task ID
        """
        task_id = f"search_{hashlib.md5(query.encode()).hexdigest()[:12]}"
        
        task = Task(
            id=task_id,
            lane=Lane.RESEARCH,
            prompt=f"Quick search: {query}\n\nUse tavily_search to find current information.",
            tools=["tavily_search"],
            context={"query": query, "agent_type": "research"},
            session_id=session_id,
            priority=priority
        )
        
        return await self.hub.enqueue(task)
