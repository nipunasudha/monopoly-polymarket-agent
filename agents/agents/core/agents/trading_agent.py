"""TradingAgent - Specialized agent for trade evaluation and execution."""

from typing import Dict, Any, Optional
from agents.core.hub import TradingHub
from agents.core.session import Lane, Task


class TradingAgent:
    """Specialized agent for trade evaluation and execution.
    
    This agent evaluates trading opportunities by:
    - Analyzing market data and current prices
    - Calculating expected value and edge
    - Making risk-aware trading decisions
    - Providing clear recommendations
    """
    
    def __init__(self, hub: TradingHub):
        """Initialize TradingAgent.
        
        Args:
            hub: TradingHub instance for task execution
        """
        self.hub = hub
        self.system_prompt = """You are a quantitative trading agent specializing in prediction markets.

Your role is to evaluate trading opportunities and make data-driven decisions.

Guidelines:
- Use get_market_data to retrieve current market information including prices, liquidity, and outcomes
- Analyze the probability implied by market prices vs your assessment
- Calculate expected value and edge (difference between your probability and market price)
- Consider risk factors: liquidity, spread, time to resolution
- Only recommend trades with significant edge (>5%) and good risk/reward
- Provide clear recommendations: BUY, SELL, or PASS
- Include position sizing recommendations based on edge and confidence
- Be conservative and risk-aware

When evaluating a trade:
1. Get current market data (prices, liquidity, spread)
2. Compare market-implied probability with your assessment
3. Calculate expected value and edge
4. Assess risk factors (liquidity, time to resolution, spread)
5. Make recommendation with reasoning
6. Suggest position size if recommending a trade

Output format:
- recommendation: "BUY", "SELL", or "PASS"
- probability: Your assessed probability (0.0-1.0)
- market_price: Current market price
- edge: Calculated edge (probability - market_price)
- confidence: Confidence level (0.0-1.0)
- position_size: Recommended position size (if not PASS)
- reasoning: Clear explanation of the decision"""
    
    async def evaluate_trade(
        self,
        market_id: str,
        research: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        priority: int = 10
    ) -> str:
        """Evaluate a trading opportunity.
        
        Args:
            market_id: Market ID or token ID to evaluate
            research: Optional research results from ResearchAgent
            session_id: Optional session ID for maintaining context
            priority: Task priority (higher = more important, default 10 for trading)
            
        Returns:
            Task ID (use hub.enqueue_and_wait() to get result)
        """
        task_id = f"trade_{market_id}"
        
        # Build evaluation prompt
        prompt_parts = [
            f"Evaluate trading opportunity for market ID: {market_id}"
        ]
        
        if research:
            prompt_parts.append("\nResearch findings:")
            if isinstance(research, dict) and "response" in research:
                prompt_parts.append(research["response"])
            else:
                prompt_parts.append(str(research))
        
        prompt_parts.extend([
            "\nPlease:",
            "1. Use get_market_data to retrieve current market information",
            "2. Analyze the market-implied probability from current prices",
            "3. Compare with your assessment (considering research if provided)",
            "4. Calculate expected value and edge",
            "5. Assess risk factors:",
            "   - Liquidity (can you exit easily?)",
            "   - Spread (transaction costs)",
            "   - Time to resolution (how long until market resolves?)",
            "6. Make a recommendation:",
            "   - BUY if you think the market is undervalued (your prob > market price + edge threshold)",
            "   - SELL if you think the market is overvalued (your prob < market price - edge threshold)",
            "   - PASS if edge is too small or risk is too high",
            "7. If recommending a trade, suggest appropriate position size",
            "8. Provide clear reasoning for your decision"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Create task
        task = Task(
            id=task_id,
            lane=Lane.MAIN,  # Trading decisions serialized
            prompt=prompt,
            tools=["get_market_data", "list_markets"],
            context={
                "market_id": market_id,
                "research": research,
                "agent_type": "trading"
            },
            session_id=session_id,
            priority=priority
        )
        
        return await self.hub.enqueue(task)
    
    async def evaluate_trade_and_wait(
        self,
        market_id: str,
        research: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        timeout: Optional[float] = 300.0
    ) -> Dict[str, Any]:
        """Evaluate trade and wait for result.
        
        Args:
            market_id: Market ID to evaluate
            research: Optional research results
            session_id: Optional session ID
            timeout: Optional timeout in seconds
            
        Returns:
            Evaluation result dictionary
        """
        task_id = f"trade_{market_id}"
        
        # Build evaluation prompt
        prompt_parts = [
            f"Evaluate trading opportunity for market ID: {market_id}"
        ]
        
        if research:
            prompt_parts.append("\nResearch findings:")
            if isinstance(research, dict) and "response" in research:
                prompt_parts.append(research["response"])
            else:
                prompt_parts.append(str(research))
        
        prompt_parts.extend([
            "\nPlease:",
            "1. Use get_market_data to retrieve current market information",
            "2. Analyze the market-implied probability from current prices",
            "3. Compare with your assessment (considering research if provided)",
            "4. Calculate expected value and edge",
            "5. Assess risk factors:",
            "   - Liquidity (can you exit easily?)",
            "   - Spread (transaction costs)",
            "   - Time to resolution (how long until market resolves?)",
            "6. Make a recommendation:",
            "   - BUY if you think the market is undervalued (your prob > market price + edge threshold)",
            "   - SELL if you think the market is overvalued (your prob < market price - edge threshold)",
            "   - PASS if edge is too small or risk is too high",
            "7. If recommending a trade, suggest appropriate position size",
            "8. Provide clear reasoning for your decision"
        ])
        
        prompt = "\n".join(prompt_parts)
        
        # Create task and wait for result
        task = Task(
            id=task_id,
            lane=Lane.MAIN,
            prompt=prompt,
            tools=["get_market_data", "list_markets"],
            context={
                "market_id": market_id,
                "research": research,
                "agent_type": "trading"
            },
            session_id=session_id,
            priority=10
        )
        
        return await self.hub.enqueue_and_wait(task, timeout=timeout)
    
    async def batch_evaluate_markets(
        self,
        market_ids: list[str],
        research_results: Optional[list[Dict[str, Any]]] = None,
        session_id: Optional[str] = None
    ) -> list[str]:
        """Evaluate multiple markets (enqueues all, returns task IDs).
        
        Args:
            market_ids: List of market IDs to evaluate
            research_results: Optional list of research results (one per market)
            session_id: Optional session ID
            
        Returns:
            List of task IDs
        """
        task_ids = []
        
        for i, market_id in enumerate(market_ids):
            research = None
            if research_results and i < len(research_results):
                research = research_results[i]
            
            task_id = await self.evaluate_trade(
                market_id=market_id,
                research=research,
                session_id=session_id,
                priority=10 - i  # Higher priority for earlier markets
            )
            task_ids.append(task_id)
        
        return task_ids
