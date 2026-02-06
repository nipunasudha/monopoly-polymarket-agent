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

            filtered_events = self.agent.filter_events_with_rag(events)
            print(f"2. FILTERED {len(filtered_events)} EVENTS")

            markets = self.agent.map_filtered_events_to_markets(filtered_events)
            print()
            print(f"3. FOUND {len(markets)} MARKETS")

            print()
            filtered_markets = self.agent.filter_markets(markets)
            print(f"4. FILTERED {len(filtered_markets)} MARKETS")

            market = filtered_markets[0]
            
            # Extract market data from the tuple (document, score)
            # The document contains the market metadata
            market_document = market[0].dict()
            market_metadata = market_document["metadata"]
            market_id = market_metadata["id"]
            market_question = market_metadata["question"]
            
            best_trade = self.agent.source_best_trade(market)
            print(f"5. CALCULATED TRADE {best_trade}")

            # Parse the trade response string to extract data
            import re
            
            # Extract probability, confidence, outcome from the LLM response
            prob_match = re.search(r'probability[:\s]+(\d+\.?\d*)', best_trade, re.IGNORECASE)
            conf_match = re.search(r'confidence[:\s]+(\d+\.?\d*)', best_trade, re.IGNORECASE)
            outcome_match = re.search(r'outcome[:\s]+(YES|NO)', best_trade, re.IGNORECASE)
            reasoning_match = re.search(r'reasoning[:\s]+(.+?)(?=\n\n|\noutcome|\nprobability|$)', best_trade, re.IGNORECASE | re.DOTALL)
            
            probability = float(prob_match.group(1)) if prob_match else 0.5
            confidence = float(conf_match.group(1)) if conf_match else 0.5
            outcome = outcome_match.group(1).upper() if outcome_match else "YES"
            reasoning = reasoning_match.group(1).strip() if reasoning_match else best_trade[:200]
            
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
            
            # Extract edge if available
            edge_match = re.search(r'edge[:\s]+(\d+\.?\d*)', best_trade, re.IGNORECASE)
            edge = float(edge_match.group(1)) if edge_match else None

            # Prepare trade data
            trade_data = {
                "market_id": str(market_id),
                "market_question": market_question,
                "outcome": outcome,
                "side": "BUY",
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
            print(f"Error: {e}")
            raise

    def maintain_positions(self):
        pass

    def incentive_farm(self):
        pass


if __name__ == "__main__":
    t = Trader()
    t.one_best_trade()
 