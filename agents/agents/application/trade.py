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

    def one_best_trade(self) -> None:
        """

        one_best_trade is a strategy that evaluates all events, markets, and orderbooks

        leverages all available information sources accessible to the autonomous agent

        then executes that trade without any human intervention

        """
        try:
            self.pre_trade_logic()

            events = self.polymarket.get_all_tradeable_events()
            print(f"1. FOUND {len(events)} EVENTS")
            
            if not events or len(events) == 0:
                print("[SKIP] No tradeable events found, skipping cycle")
                return

            filtered_events = self.agent.filter_events_with_rag(events)
            print(f"2. FILTERED {len(filtered_events)} EVENTS")
            
            if not filtered_events or len(filtered_events) == 0:
                print("[SKIP] No events passed filtering, skipping cycle")
                return

            markets = self.agent.map_filtered_events_to_markets(filtered_events)
            print()
            print(f"3. FOUND {len(markets)} MARKETS")
            
            if not markets or len(markets) == 0:
                print("[SKIP] No markets found, skipping cycle")
                return

            print()
            filtered_markets = self.agent.filter_markets(markets)
            print(f"4. FILTERED {len(filtered_markets)} MARKETS")
            
            if not filtered_markets or len(filtered_markets) == 0:
                print("[SKIP] No markets passed filtering, skipping cycle")
                return

            # Safely get the first market
            market = filtered_markets[0]
            
            # Validate market structure
            if not isinstance(market, tuple) or len(market) < 2:
                print(f"[ERROR] Invalid market format: {type(market)}, skipping cycle")
                return
            
            # Extract market data from the tuple (document, score)
            # The document contains the market metadata
            try:
                market_document = market[0].dict()
                market_metadata = market_document.get("metadata", {})
                market_id = market_metadata.get("id")
                market_question = market_metadata.get("question", "Unknown Market")
                
                if not market_id:
                    print("[ERROR] Market ID not found in metadata, skipping cycle")
                    return
            except (AttributeError, KeyError, TypeError) as e:
                print(f"[ERROR] Failed to extract market data: {e}, skipping cycle")
                return
            
            best_trade = self.agent.source_best_trade(market)
            print(f"5. CALCULATED TRADE {best_trade}")

            # Parse the trade response string to extract data
            import re
            
            # Extract probability, confidence, outcome from the LLM response
            # Handle both decimal (0.65) and percentage (65) formats
            prob_match = re.search(r'probability[:\s]+(\d+\.?\d*)', best_trade, re.IGNORECASE)
            conf_match = re.search(r'confidence[:\s]+(\d+\.?\d*)', best_trade, re.IGNORECASE)
            outcome_match = re.search(r'outcome[:\s]+(YES|NO|Yes|No)', best_trade, re.IGNORECASE)
            reasoning_match = re.search(r'reasoning[:\s]+(.+?)(?=\n\n|\noutcome|\nprobability|RESPONSE|$)', best_trade, re.IGNORECASE | re.DOTALL)
            
            probability = float(prob_match.group(1)) if prob_match else 0.5
            # Normalize if it's > 1 (percentage format)
            if probability > 1.0:
                probability = probability / 100.0
            
            confidence = float(conf_match.group(1)) if conf_match else 0.5
            if confidence > 1.0:
                confidence = confidence / 100.0
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            outcome = outcome_match.group(1).upper() if outcome_match else "YES"
            reasoning = reasoning_match.group(1).strip() if reasoning_match else best_trade[:500]
            
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

            amount = self.agent.format_trade_prompt_for_execution(best_trade)
            
            # Extract side and edge from trade response
            side_match = re.search(r'side[:\s]+(BUY|SELL)', best_trade, re.IGNORECASE)
            edge_match = re.search(r'edge[:\s]+(\d+\.?\d*)', best_trade, re.IGNORECASE)
            
            side = side_match.group(1).upper() if side_match else "BUY"
            edge = float(edge_match.group(1)) if edge_match else None
            if edge and edge > 1.0:
                edge = edge / 100.0  # Normalize if percentage

            # Prepare trade data
            trade_data = {
                "market_id": str(market_id),
                "market_question": market_question,
                "outcome": outcome,
                "side": side,
                "size": float(amount),
                "forecast_probability": probability,
                "edge": edge,
                "status": "pending",
                "execution_enabled": not self.dry_run,
            }

            if self.dry_run:
                print()
                print("=" * 60)
                print("[DRY RUN] Trade recommendation (not executed)")
                print(f"  Amount: ${amount:.2f} USDC")
                print(f"  Details: {best_trade}")
                print("=" * 60)
                print()
                print("Set TRADING_MODE=live in .env to execute trades.")
                
                # Save trade as simulated
                trade_data["status"] = "simulated"
                saved_trade = self.db.save_trade(trade_data)
                print(f"   Saved trade ID: {saved_trade.id}")
            else:
                # Request approval for large trades if approval manager is configured
                approved = True
                if self.approval_manager:
                    # Generate trade ID
                    import uuid
                    trade_id = str(uuid.uuid4())
                    trade_data["trade_id"] = trade_id
                    
                    # Calculate size as fraction of balance for threshold check
                    try:
                        balance = self.polymarket.get_usdc_balance()
                        size_fraction = amount / balance if balance > 0 else 0
                        trade_data["size_fraction"] = size_fraction
                    except Exception as e:
                        print(f"[WARNING] Could not get balance for approval check: {e}")
                        size_fraction = 0
                    
                    # Request approval (this will block if needed)
                    try:
                        # Run async approval in sync context
                        approved = asyncio.run(
                            self.approval_manager.request_approval(
                                trade_id=trade_id,
                                trade_data=trade_data,
                                timeout=300
                            )
                        )
                    except Exception as e:
                        print(f"[ERROR] Approval request failed: {e}")
                        approved = False
                    
                    if not approved:
                        print("[REJECTED] Trade rejected by operator or timed out")
                        trade_data["status"] = "rejected"
                        saved_trade = self.db.save_trade(trade_data)
                        print(f"   Saved rejected trade ID: {saved_trade.id}")
                        return
                
                # Execute trade if approved
                # Please refer to TOS before enabling: polymarket.com/tos
                trade = self.polymarket.execute_market_order(market, amount)
                print(f"6. TRADED {trade}")
                
                # Update trade data with execution details
                trade_data["status"] = "executed"
                trade_data["executed_at"] = trade.get("executed_at")
                trade_data["transaction_hash"] = trade.get("transaction_hash")
                trade_data["price"] = trade.get("price")
                saved_trade = self.db.save_trade(trade_data)
                print(f"   Saved trade ID: {saved_trade.id}")

        except Exception as e:
            print(f"[ERROR] Trade execution failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't re-raise - let the agent continue to next cycle
            # This prevents the entire agent from crashing on a single failed cycle
    
    async def one_best_trade_v2(self, hub, research_agent, trading_agent) -> None:
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
    t = Trader()
    t.one_best_trade()
 