# Monopoly Polymarket Agent System — metarunelabs.dev
import os
import json
import ast
import re
from typing import List, Dict, Any

import math

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic

from agents.polymarket.gamma import GammaMarketClient as Gamma
from agents.connectors.chroma import PolymarketRAG as Chroma
from agents.utils.objects import SimpleEvent, SimpleMarket
from agents.application.prompts import Prompter
from agents.polymarket.polymarket import Polymarket

def retain_keys(data, keys_to_retain):
    if isinstance(data, dict):
        return {
            key: retain_keys(value, keys_to_retain)
            for key, value in data.items()
            if key in keys_to_retain
        }
    elif isinstance(data, list):
        return [retain_keys(item, keys_to_retain) for item in data]
    else:
        return data

class Executor:
    def __init__(self, default_model='claude-sonnet-4-20250514') -> None:
        load_dotenv()
        self.token_limit = 180000
        self.prompter = Prompter()
        self.dry_run = os.getenv("TRADING_MODE", "dry_run").lower() != "live"
        
        # Skip LLM initialization in dry_run mode
        if not self.dry_run:
            self.llm = ChatAnthropic(
                model=default_model,
                temperature=0,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            )
        else:
            self.llm = None
            print("[DRY RUN] Executor initialized in fast mode (no LLM calls)")
        
        self.gamma = Gamma()
        self.chroma = Chroma()
        self.polymarket = Polymarket()

    def get_llm_response(self, user_input: str) -> str:
        if self.dry_run:
            return "Mock LLM response: This market shows interesting opportunity based on recent trends."
        system_message = SystemMessage(content=str(self.prompter.market_analyst()))
        human_message = HumanMessage(content=user_input)
        messages = [system_message, human_message]
        result = self.llm.invoke(messages)
        return result.content

    def get_superforecast(
        self, event_title: str, market_question: str, outcome: str
    ) -> str:
        if self.dry_run:
            import random
            prob = random.uniform(0.3, 0.7)
            return f"[DRY RUN] Mock forecast: I estimate a {prob:.1%} probability for {outcome} based on historical patterns and market analysis."
        messages = self.prompter.superforecaster(
            description=event_title, question=market_question, outcome=outcome
        )
        result = self.llm.invoke(messages)
        return result.content


    def estimate_tokens(self, text: str) -> int:
        # This is a rough estimate. For more accurate results, consider using a tokenizer.
        return len(text) // 4  # Assuming average of 4 characters per token

    def process_data_chunk(self, data1: List[Dict[Any, Any]], data2: List[Dict[Any, Any]], user_input: str) -> str:
        system_message = SystemMessage(
            content=str(self.prompter.prompts_polymarket(data1=data1, data2=data2))
        )
        human_message = HumanMessage(content=user_input)
        messages = [system_message, human_message]
        result = self.llm.invoke(messages)
        return result.content


    def divide_list(self, original_list, i):
        # Calculate the size of each sublist
        sublist_size = math.ceil(len(original_list) / i)
        
        # Use list comprehension to create sublists
        return [original_list[j:j+sublist_size] for j in range(0, len(original_list), sublist_size)]
    
    def get_polymarket_llm(self, user_input: str) -> str:
        data1 = self.gamma.get_current_events()
        data2 = self.gamma.get_current_markets()
        
        combined_data = str(self.prompter.prompts_polymarket(data1=data1, data2=data2))
        
        # Estimate total tokens
        total_tokens = self.estimate_tokens(combined_data)
        
        # Set a token limit (adjust as needed, leaving room for system and user messages)
        token_limit = self.token_limit
        if total_tokens <= token_limit:
            # If within limit, process normally
            return self.process_data_chunk(data1, data2, user_input)
        else:
            # If exceeding limit, process in chunks
            chunk_size = len(combined_data) // ((total_tokens // token_limit) + 1)
            print(f'total tokens {total_tokens} exceeding llm capacity, now will split and answer')
            group_size = (total_tokens // token_limit) + 1 # 3 is safe factor
            keys_no_meaning = ['image','pagerDutyNotificationEnabled','resolvedBy','endDate','clobTokenIds','negRiskMarketID','conditionId','updatedAt','startDate']
            useful_keys = ['id','questionID','description','liquidity','clobTokenIds','outcomes','outcomePrices','volume','startDate','endDate','question','questionID','events']
            data1 = retain_keys(data1, useful_keys)
            cut_1 = self.divide_list(data1, group_size)
            cut_2 = self.divide_list(data2, group_size)
            cut_data_12 = zip(cut_1, cut_2)

            results = []

            for cut_data in cut_data_12:
                sub_data1 = cut_data[0]
                sub_data2 = cut_data[1]
                sub_tokens = self.estimate_tokens(str(self.prompter.prompts_polymarket(data1=sub_data1, data2=sub_data2)))

                result = self.process_data_chunk(sub_data1, sub_data2, user_input)
                results.append(result)
            
            combined_result = " ".join(results)
            
        
            
            return combined_result
    def filter_events(self, events: "list[SimpleEvent]") -> str:
        prompt = self.prompter.filter_events(events)
        result = self.llm.invoke(prompt)
        return result.content

    def filter_events_with_rag(self, events: "list[SimpleEvent]") -> str:
        prompt = self.prompter.filter_events()
        print()
        print("... prompting ... ", prompt)
        print()
        return self.chroma.events(events, prompt)

    def map_filtered_events_to_markets(
        self, filtered_events: "list[SimpleEvent]"
    ) -> "list[SimpleMarket]":
        if self.dry_run:
            # Skip expensive API calls - just create mock markets
            print("[DRY RUN] Fast mode: creating mock markets (no API calls)")
            markets = []
            for e in filtered_events[:2]:  # Only process first 2 for speed
                data = json.loads(e[0].json())
                market_ids = data["metadata"]["markets"].split(",")
                # Just use first market ID, create mock data
                market_id = market_ids[0] if market_ids else "mock_id"
                mock_market = {
                    "id": market_id,
                    "question": data["page_content"][:100],
                    "description": data["page_content"],
                    "outcomes": ["Yes", "No"],
                    "outcome_prices": ["0.45", "0.55"],
                    "clob_token_ids": ["123", "456"]
                }
                markets.append(mock_market)
            return markets
        
        markets = []
        for e in filtered_events:
            data = json.loads(e[0].json())
            market_ids = data["metadata"]["markets"].split(",")
            for market_id in market_ids:
                market_data = self.gamma.get_market(market_id)
                formatted_market_data = self.polymarket.map_api_to_market(market_data)
                markets.append(formatted_market_data)
        return markets

    def filter_markets(self, markets) -> "list[tuple]":
        prompt = self.prompter.filter_markets()
        print()
        print("... prompting ... ", prompt)
        print()
        return self.chroma.markets(markets, prompt)

    def source_best_trade(self, market_object) -> str:
        if self.dry_run:
            import random
            # Generate fast mock trade
            prob = random.uniform(0.3, 0.7)
            price = random.uniform(0.3, 0.7)
            size = random.uniform(0.05, 0.15)
            side = random.choice(["BUY", "SELL"])
            
            market_document = market_object[0].dict()
            market = market_document["metadata"]
            question = market.get("question", "Mock Market Question")
            
            mock_response = f"""
            [DRY RUN] Fast mock analysis for: {question[:100]}
            
            Analysis: Based on historical patterns and market dynamics, this represents an interesting opportunity.
            
            RESPONSE```
            price:{price:.3f},
            size:{size:.2f},
            side:{side},
            ```
            """
            print(f"[DRY RUN] Generated mock trade instantly")
            return mock_response
        
        market_document = market_object[0].dict()
        market = market_document["metadata"]
        outcome_prices = ast.literal_eval(market["outcome_prices"])
        outcomes = ast.literal_eval(market["outcomes"])
        question = market["question"]
        description = market_document["page_content"]

        prompt = self.prompter.superforecaster(question, description, outcomes)
        print()
        print("... prompting ... ", prompt)
        print()
        result = self.llm.invoke(prompt)
        content = result.content

        print("result: ", content)
        print()
        prompt = self.prompter.one_best_trade(content, outcomes, outcome_prices)
        print("... prompting ... ", prompt)
        print()
        result = self.llm.invoke(prompt)
        content = result.content

        print("result: ", content)
        print()
        return content

    def format_trade_prompt_for_execution(self, best_trade: str) -> float:
        # Extract size from the RESPONSE block (e.g. "size:0.25")
        size_match = re.search(r'size\s*:\s*(\d+\.?\d*)', best_trade)
        if not size_match:
            raise ValueError(f"Could not parse size from trade response: {best_trade[-200:]}")
        size = float(size_match.group(1))
        usdc_balance = self.polymarket.get_usdc_balance()
        return size * usdc_balance

    def source_best_market_to_create(self, filtered_markets) -> str:
        prompt = self.prompter.create_new_market(filtered_markets)
        print()
        print("... prompting ... ", prompt)
        print()
        result = self.llm.invoke(prompt)
        content = result.content
        return content
