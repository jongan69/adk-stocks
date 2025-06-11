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
from .tools.risk import (
    check_position_size,
    check_volatility
)
import collections

# Helper function to get sector for a stock using Finviz overview
def get_stock_sector(ticker):
    try:
        overview = get_screener_overview_tool({'Ticker': ticker})
        if overview and 'Sector' in overview[0]:
            return overview[0]['Sector']
    except Exception:
        pass
    return None

# Helper function to get current portfolio context
def get_portfolio_context():
    positions = get_all_positions()
    held_symbols = [pos['symbol'] for pos in positions]
    # Get sector exposure
    sector_counts = collections.Counter()
    for symbol in held_symbols:
        sector = get_stock_sector(symbol)
        if sector:
            sector_counts[sector] += 1
    # Estimate portfolio volatility (mean of held stocks)
    volatilities = []
    for symbol in held_symbols:
        try:
            vol = calculate_volatility(symbol)
            if vol is not None:
                volatilities.append(vol)
        except Exception:
            pass
    avg_volatility = sum(volatilities) / len(volatilities) if volatilities else None
    return {
        "held_symbols": held_symbols,
        "sector_counts": sector_counts,
        "avg_volatility": avg_volatility
    }

def infer_risk_profile(avg_volatility):
    # Simple heuristic: <0.03 = low, <0.06 = medium, else high
    if avg_volatility is None:
        return 'medium'
    if avg_volatility < 0.03:
        return 'low'
    elif avg_volatility < 0.06:
        return 'medium'
    else:
        return 'high'

# Example function to recommend stocks using dynamic portfolio context
def recommend_stocks(user_preferences=None, limit=20):
    context = get_portfolio_context()
    held_symbols = context["held_symbols"]
    sector_counts = context["sector_counts"]
    avg_volatility = context["avg_volatility"]
    # Infer risk profile if not provided
    risk_profile = user_preferences.get('risk') if user_preferences and 'risk' in user_preferences else infer_risk_profile(avg_volatility)
    # Identify underrepresented sector(s)
    if sector_counts:
        min_count = min(sector_counts.values())
        underrepresented_sectors = [s for s, c in sector_counts.items() if c == min_count]
    else:
        underrepresented_sectors = None
    high_volume_stocks = get_highest_volume_tool(limit=limit)
    candidates = []
    explanations = []
    for stock in high_volume_stocks:
        ticker = stock.get('Ticker')
        if ticker in held_symbols:
            continue
        sector = stock.get('Sector') or get_stock_sector(ticker)
        if underrepresented_sectors and sector and sector not in underrepresented_sectors:
            continue  # Prefer underrepresented sectors
        vol = None
        try:
            vol = calculate_volatility(ticker)
        except Exception:
            pass
        # Risk filtering
        if risk_profile == 'low' and vol and vol > 0.03:
            continue
        if risk_profile == 'medium' and vol and vol > 0.06:
            continue
        # Add explanation
        explanation = f"{ticker}: Sector={sector or 'N/A'}, Volatility={vol if vol is not None else 'N/A'}, Reason: "
        if sector and underrepresented_sectors and sector in underrepresented_sectors:
            explanation += "diversifies sector exposure; "
        if vol is not None:
            if risk_profile == 'low' and vol <= 0.03:
                explanation += "fits low risk profile; "
            elif risk_profile == 'medium' and vol <= 0.06:
                explanation += "fits medium risk profile; "
            elif risk_profile == 'high':
                explanation += "fits high risk profile; "
        candidates.append(stock)
        explanations.append(explanation)
        if len(candidates) >= 5:
            break
    if not candidates:
        return "No suitable recommendations found based on your portfolio's sector exposure and risk profile."
    return list(zip(candidates, explanations))

# Define the Market Research Agent
market_research_agent = Agent(
    name="market_research_agent",
    model="gemini-2.0-flash",
    description="Performs market research using Yahoo Finance and Finviz.",
    instruction="When asked for stock recommendations, always retrieve the current Alpaca portfolio using get_all_positions and use this context to filter out already-held stocks and diversify recommendations. Then retrieve a list of high volume stocks using get_highest_volume_tool, and use other research tools to narrow down the list based on additional criteria.",
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

# Define the Risk Management Agent
risk_management_agent = Agent(
    name="risk_management_agent",
    model="gemini-2.0-flash",
    description="Evaluates trade ideas for risk and compliance.",
    instruction="Check proposed trades for position size and volatility limits.",
    tools=[
        check_position_size,
        check_volatility
    ]
)

# Define the Root Agent (Team Orchestrator)
root_agent = Agent(
    name="market_team_orchestrator",
    model="gemini-2.0-flash",
    description="Delegates market research, risk, and trading tasks to specialist agents.",
    instruction="Delegate market research to the market_research_agent, risk checks to risk_management_agent, and trading tasks to the trade_execution_agent.",
    tools=[],
    sub_agents=[market_research_agent, risk_management_agent, trade_execution_agent]
)