from google.adk.agents import Agent
from .tools.research import (
    get_screener_overview_tool,
    get_screener_valuation_tool,
    get_screener_financial_tool,
    get_highest_volume_tool,
    get_stock_price,
    get_all_fundamental_metrics
)
from .tools.trading import (
    get_all_positions,
    get_account_value,
    get_open_orders,
    buy_stock_asset,
    sell_stock_asset,
    get_high_open_interest_contracts,
    get_corporate_actions_by_symbol,
    get_historical_data,
    calculate_volatility
)

# Define the Market Research Agent
market_research_agent = Agent(
    name="market_research_agent",
    model="gemini-2.0-flash",
    description="Performs market research using Yahoo Finance and Finviz.",
    instruction="When asked for stock recommendations, first retrieve a list of high volume stocks using get_highest_volume_tool, then use other research tools to narrow down the list based on additional criteria. Use the current Alpaca portfolio (via get_all_positions) for context to avoid suggesting stocks already held or to diversify recommendations.",
    tools=[
        get_screener_overview_tool,
        get_screener_valuation_tool,
        get_screener_financial_tool,
        get_highest_volume_tool,
        get_stock_price,
        get_all_fundamental_metrics,
        get_all_positions
    ]
)

# Define the Trade Execution Agent
trade_execution_agent = Agent(
    name="trade_execution_agent",
    model="gemini-2.0-flash",
    description="Executes trades and manages orders via Alpaca.",
    instruction="Use your tools to place, modify, or cancel trades as instructed.",
    tools=[
        get_all_positions,
        get_account_value,
        get_open_orders,
        buy_stock_asset,
        sell_stock_asset,
        get_high_open_interest_contracts,
        get_corporate_actions_by_symbol,
        get_historical_data,
        calculate_volatility
    ]
)

# Define the Root Agent (Team Orchestrator)
root_agent = Agent(
    name="market_team_orchestrator",
    model="gemini-2.0-flash",
    description="Delegates market research and trading tasks to specialist agents.",
    instruction="Delegate market research to the market_research_agent and trading tasks to the trade_execution_agent.",
    tools=[],
    sub_agents=[market_research_agent, trade_execution_agent]
)