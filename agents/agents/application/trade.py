# Monopoly Polymarket Agent System — metarunelabs.dev
import os
import asyncio
from typing import Optional
from agents.application.executor import Executor as Agent
from agents.polymarket.gamma import GammaMarketClient as Gamma
from agents.polymarket.polymarket import Polymarket
from agents.connectors.database import Database
from agents.core.approvals import ApprovalManager

import shutil


class Trader:
    def __init__(self, approval_manager: Optional[ApprovalManager] = None):
        self.dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
        self.polymarket = Polymarket()
        self.gamma = Gamma()
        self.agent = Agent()
        self.db = Database()  # Add database connection
        self.approval_manager = approval_manager

    def pre_trade_logic(self) -> None:
        self.clear_local_dbs()

    def clear_local_dbs(self) -> None:
        try:
            shutil.rmtree("local_db_events")
        except:
            pass
        try:
            shutil.rmtree("local_db_markets")
        except:
            pass

    async def one_best_trade(self, hub, research_agent, trading_agent) -> None:
        """
        New version using TradingHub and specialized agents (Phase 7).
        
        Flow:
        1. Get events (existing RAG filtering)
        2. Parallel research on top markets
        3. Sequential trade evaluation (MAIN lane, concurrency 1)
        4. Approval workflow (existing)
        5. Execute trade (existing)
        
        Args:
            hub: TradingHub instance
            research_agent: ResearchAgent instance
            trading_agent: TradingAgent instance
        """
        try:
            self.pre_trade_logic()
            
            # 1. Get and filter events (existing RAG)
            events = self.polymarket.get_all_tradeable_events()
            print(f"1. FOUND {len(events)} EVENTS")
            
            if not events or len(events) == 0:
                print("[SKIP] No tradeable events found")
                return
            
            filtered_events = self.agent.filter_events_with_rag(events)
            print(f"2. FILTERED {len(filtered_events)} EVENTS")
            
            if not filtered_events or len(filtered_events) == 0:
                print("[SKIP] No events passed filtering")
                return
            
            markets = self.agent.map_filtered_events_to_markets(filtered_events)
            print(f"3. FOUND {len(markets)} MARKETS")
            
            if not markets or len(markets) == 0:
                print("[SKIP] No markets found")
                return
            
            # 2. NEW: Parallel research on top 3 markets
            top_markets = markets[:3]
            print(f"4. RESEARCHING TOP {len(top_markets)} MARKETS (parallel)...")
            
            research_results = []
            for market in top_markets:
                market_question = market.get("question", "")
                market_description = market.get("description", "")
                
                if not market_question:
                    research_results.append(None)
                    continue
                
                # Research in parallel (RESEARCH lane, concurrency 3)
                try:
                    result = await research_agent.research_market_and_wait(
                        market_question=market_question,
                        market_description=market_description,
                        timeout=120.0  # 2 minute timeout
                    )
                    research_results.append(result)
                    print(f"   Research completed for: {market_question[:60]}...")
                except Exception as e:
                    print(f"   Research failed for {market_question[:60]}: {e}")
                    research_results.append(None)
            
            print(f"5. COMPLETED RESEARCH ON {len(research_results)} MARKETS")
            
            # 3. NEW: Sequential trade evaluation (MAIN lane, concurrency 1)
            for i, market in enumerate(top_markets):
                market_id = market.get("id")
                if not market_id:
                    continue
                
                market_question = market.get("question", "Unknown Market")
                
                # Evaluate trade with research context
                print(f"6. EVALUATING TRADE FOR: {market_question[:60]}...")
                try:
                    trade_eval = await trading_agent.evaluate_trade_and_wait(
                        market_id=market_id,
                        research=research_results[i],
                        timeout=120.0
                    )
                except Exception as e:
                    print(f"   Trade evaluation failed: {e}")
                    continue
                
                if not trade_eval.get("success"):
                    print(f"   [SKIP] Evaluation failed: {trade_eval.get('error')}")
                    continue
                
                response_text = trade_eval.get("response", "")
                print(f"7. TRADE EVALUATION: {response_text[:200]}...")
                
                # Check if recommendation is PASS
                if "PASS" in response_text.upper() and "recommendation" in response_text.lower():
                    print("   [SKIP] Recommendation is PASS")
                    continue
                
                # Parse trade details (same as existing one_best_trade)
                import re
                
                prob_match = re.search(r'probability[:\s]+(\d+\.?\d*)', response_text, re.IGNORECASE)
                conf_match = re.search(r'confidence[:\s]+(\d+\.?\d*)', response_text, re.IGNORECASE)
                outcome_match = re.search(r'outcome[:\s]+(YES|NO|Yes|No)', response_text, re.IGNORECASE)
                side_match = re.search(r'side[:\s]+(BUY|SELL)', response_text, re.IGNORECASE)
                size_match = re.search(r'size[:\s]+(\d+\.?\d*)', response_text, re.IGNORECASE)
                edge_match = re.search(r'edge[:\s]+(\d+\.?\d*)', response_text, re.IGNORECASE)
                reasoning_match = re.search(r'reasoning[:\s]+(.+?)(?=\n\n|\noutcome|\nprobability|RESPONSE|$)', response_text, re.IGNORECASE | re.DOTALL)
                
                if not all([prob_match, side_match, size_match]):
                    print("   [SKIP] Could not parse required trade details")
                    continue
                
                probability = float(prob_match.group(1))
                if probability > 1.0:
                    probability /= 100.0
                
                confidence = float(conf_match.group(1)) if conf_match else 0.5
                if confidence > 1.0:
                    confidence /= 100.0
                confidence = max(0.0, min(1.0, confidence))
                
                outcome = outcome_match.group(1).upper() if outcome_match else "YES"
                side = side_match.group(1).upper()
                size_fraction = float(size_match.group(1))
                
                edge = float(edge_match.group(1)) if edge_match else None
                if edge and edge > 1.0:
                    edge /= 100.0
                
                reasoning = reasoning_match.group(1).strip() if reasoning_match else response_text[:500]
                
                # Calculate amount
                usdc_balance = self.polymarket.get_usdc_balance()
                amount = size_fraction * usdc_balance
                
                print(f"8. CALCULATED TRADE: {side} {outcome} {amount:.2f} USDC (prob: {probability:.1%}, edge: {edge:.1%})" if edge else f"8. CALCULATED TRADE: {side} {outcome} {amount:.2f} USDC (prob: {probability:.1%})")
                
                # Save forecast to database
                forecast_data = {
                    "market_id": str(market_id),
                    "market_question": market_question,
                    "outcome": outcome,
                    "probability": probability,
                    "confidence": confidence,
                    "reasoning": reasoning,
                }
                saved_forecast = self.db.save_forecast(forecast_data)
                print(f"   Saved forecast ID: {saved_forecast.id}")
                
                # 4. Approval workflow (existing)
                if not self.dry_run and self.approval_manager:
                    import uuid
                    trade_id = str(uuid.uuid4())
                    
                    trade_data = {
                        "trade_id": trade_id,
                        "market_id": market_id,
                        "market_question": market_question,
                        "outcome": outcome,
                        "side": side,
                        "size": size_fraction,
                        "amount": amount,
                        "probability": probability,
                        "confidence": confidence,
                        "edge": edge,
                    }
                    
                    approved = await self.approval_manager.request_approval(
                        trade_id=trade_id,
                        trade_data=trade_data
                    )
                    
                    if not approved:
                        print("   [REJECTED] Trade not approved")
                        
                        # Save rejected trade to database
                        trade_data_db = {
                            "market_id": str(market_id),
                            "market_question": market_question,
                            "outcome": outcome,
                            "side": side,
                            "amount": amount,
                            "probability": probability,
                            "confidence": confidence,
                            "edge": edge,
                            "status": "rejected",
                        }
                        saved_trade = self.db.save_trade(trade_data_db)
                        print(f"   Saved rejected trade ID: {saved_trade.id}")
                        continue
                
                # 5. Execute trade (existing)
                if not self.dry_run:
                    print(f"9. EXECUTING TRADE on market {market_id}")
                    
                    # Prepare trade data for database
                    trade_data_db = {
                        "market_id": str(market_id),
                        "market_question": market_question,
                        "outcome": outcome,
                        "side": side,
                        "amount": amount,
                        "probability": probability,
                        "confidence": confidence,
                        "edge": edge,
                        "status": "pending",
                    }
                    
                    # Execute the actual trade
                    trade = self.polymarket.execute_market_order(market, amount)
                    print(f"10. TRADED {trade}")
                    
                    # Update with execution details
                    trade_data_db["status"] = "executed"
                    trade_data_db["executed_at"] = trade.get("executed_at")
                    trade_data_db["transaction_hash"] = trade.get("transaction_hash")
                    trade_data_db["price"] = trade.get("price")
                    saved_trade = self.db.save_trade(trade_data_db)
                    print(f"   Saved trade ID: {saved_trade.id}")
                else:
                    print(f"9. [DRY RUN] Would execute: {side} {outcome} @ {probability:.1%}" + (f" (edge: {edge:.1%})" if edge else ""))
                
                # Only execute one trade per cycle
                break
        
        except Exception as e:
            print(f"[ERROR] Trade cycle failed: {e}")
            import traceback
            traceback.print_exc()

    def maintain_positions(self):
        pass

    def incentive_farm(self):
        pass


if __name__ == "__main__":
    import asyncio
    from agents.core.hub import TradingHub
    from agents.core.agents import ResearchAgent, TradingAgent
    
    async def main():
        t = Trader()
        hub = TradingHub()
        research_agent = ResearchAgent(hub)
        trading_agent = TradingAgent(hub)
        
        await hub.start()
        await t.one_best_trade(hub, research_agent, trading_agent)
        await hub.stop()
    
    asyncio.run(main())
 