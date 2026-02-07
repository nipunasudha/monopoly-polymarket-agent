#!/usr/bin/env python3
"""
Script to clean up trade.py by replacing one_best_trade with one_best_trade_v2
and removing the old implementation.
"""
import re

# Read the file
with open("agents/application/trade.py", "r") as f:
    content = f.read()

# Find the start of one_best_trade_v2
v2_start = content.find("async def one_best_trade_v2(")
if v2_start == -1:
    print("ERROR: Could not find one_best_trade_v2")
    exit(1)

# Find the end of one_best_trade_v2 (next method definition or end of class)
v2_section = content[v2_start:]
# Find the next method at same indentation level
next_method = re.search(r'\n    def \w+\(', v2_section[100:])  # Skip first 100 chars to avoid matching itself
if next_method:
    v2_end = v2_start + 100 + next_method.start()
    v2_content = content[v2_start:v2_end]
else:
    print("ERROR: Could not find end of one_best_trade_v2")
    exit(1)

# Find and remove the old one_best_trade method
old_start = content.find("def one_best_trade(self) -> None:")
if old_start == -1:
    print("ERROR: Could not find old one_best_trade")
    exit(1)

# Find where the old method ends (at one_best_trade_v2)
old_end = v2_start

# Extract parts
before_old = content[:old_start]
after_v2 = content[v2_end:]

# Rename v2 to main and update signature
v2_content_renamed = v2_content.replace(
    "async def one_best_trade_v2(self, hub, research_agent, trading_agent) -> None:",
    "async def one_best_trade(self, hub, research_agent, trading_agent) -> None:"
)
v2_content_renamed = v2_content_renamed.replace(
    '"""\\n        New version using TradingHub and specialized agents (Phase 7).',
    '"""\\n        Execute one best trade using the OpenClaw architecture with TradingHub.'
)

# Combine
new_content = before_old + v2_content_renamed + after_v2

# Update the __main__ section
new_content = new_content.replace(
    '''if __name__ == "__main__":
    t = Trader()
    t.one_best_trade()''',
    '''if __main__ == "__main__":
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
    
    asyncio.run(main())'''
)

# Write back
with open("agents/application/trade.py", "w") as f:
    f.write(new_content)

print("✓ Successfully cleaned up trade.py")
print(f"  - Replaced one_best_trade with one_best_trade_v2 content")
print(f"  - Removed old legacy implementation")
print(f"  - Updated __main__ section")
