# Monopoly Polymarket Agent System — metarunelabs.dev
import os
from agents.application.executor import Executor as Agent
from agents.polymarket.gamma import GammaMarketClient as Gamma
from agents.polymarket.polymarket import Polymarket
from agents.connectors.database import Database

import shutil


class Trader:
    def __init__(self):
        self.dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
        self.polymarket = Polymarket()
        self.gamma = Gamma()
        self.agent = Agent()
        self.db = Database()  # Add database connection

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

    def maintain_positions(self):
        pass

    def incentive_farm(self):
        pass


if __name__ == "__main__":
    t = Trader()
    t.one_best_trade()
 