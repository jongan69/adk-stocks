import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
from alpaca.trading.client import TradingClient
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest, StockBarsRequest, StockLatestQuoteRequest, StockSnapshotRequest
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest, GetOptionContractsRequest, GetCorporateAnnouncementsRequest
from alpaca.trading.enums import QueryOrderStatus, OrderSide, TimeInForce, AssetStatus, ExerciseStyle
from alpaca.common.exceptions import APIError
from alpaca.data.timeframe import TimeFrame

# Load API keys from environment
ALPACA_API_KEY = os.getenv("ALPACA_API_LIVE_KEY")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
ALPACA_API_KEY_PAPER = os.getenv("ALPACA_API_PAPER_KEY")
ALPACA_API_SECRET_PAPER = os.getenv("ALPACA_API_SECRET_PAPER")
IS_DEVELOPMENT = False

# Initialize clients
if IS_DEVELOPMENT:
    trading_client = TradingClient(ALPACA_API_KEY_PAPER, ALPACA_API_SECRET_PAPER, paper=True)
    data_client = StockHistoricalDataClient(ALPACA_API_KEY_PAPER, ALPACA_API_SECRET_PAPER)
else:
    trading_client = TradingClient(ALPACA_API_KEY, ALPACA_API_SECRET, paper=False)
    data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_API_SECRET)

# --- Trading Tools for ADK Agent ---
def _convert_uuids_to_str(obj):
    if isinstance(obj, dict):
        return {k: _convert_uuids_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_uuids_to_str(i) for i in obj]
    elif hasattr(obj, 'hex') and hasattr(obj, 'int'):
        # likely a UUID
        return str(obj)
    else:
        return obj

def get_all_positions() -> List[dict]:
    """
    Returns all current positions in the Alpaca account.
    Returns:
        List[dict]: List of position details.
    """
    positions = trading_client.get_all_positions()
    return [_convert_uuids_to_str(p.__dict__) for p in positions]

def get_account_value() -> float:
    """
    Returns the current account portfolio value.
    Returns:
        float: Portfolio value in USD.
    """
    account = trading_client.get_account()
    return float(account.portfolio_value)

def get_open_orders() -> List[dict]:
    """
    Returns all open orders in the Alpaca account.
    Returns:
        List[dict]: List of open order details.
    """
    orders = trading_client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=50))
    return [_convert_uuids_to_str(o.__dict__) for o in orders]

def buy_stock_asset(symbol: str, qty: Optional[int] = None) -> str:
    """
    Places a buy order for a stock asset.
    Args:
        symbol (str): Stock symbol to buy.
        qty (int, optional): Quantity to buy. If not specified, will buy 1 share.
    Returns:
        str: Result message.
    """
    from alpaca.trading.requests import MarketOrderRequest
    if qty is None:
        qty = 1
    order_request = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order_data=order_request)
    return f"Buy order placed for {qty} shares of {symbol}."

def sell_stock_asset(symbol: str, qty: Optional[int] = None) -> str:
    """
    Places a sell order for a stock asset.
    Args:
        symbol (str): Stock symbol to sell.
        qty (int, optional): Quantity to sell. If not specified, will sell all available.
    Returns:
        str: Result message.
    """
    from alpaca.trading.requests import MarketOrderRequest
    positions = trading_client.get_all_positions()
    position = next((p for p in positions if p.symbol == symbol), None)
    if not position:
        return f"No position found for {symbol}."
    qty_to_sell = qty if qty is not None else int(float(position.qty))
    order_request = MarketOrderRequest(
        symbol=symbol,
        qty=qty_to_sell,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.DAY
    )
    trading_client.submit_order(order_data=order_request)
    return f"Sell order placed for {qty_to_sell} shares of {symbol}."

def get_high_open_interest_contracts(ticker: str, option_type: str = "call") -> dict:
    """
    Fetches high open-interest option contracts for a ticker.
    Args:
        ticker (str): Stock symbol.
        option_type (str): 'call' or 'put'.
    Returns:
        dict: Short-term and LEAP contracts with highest open interest.
    """
    now = datetime.now(timezone.utc)
    short_term_expiration_gte = (now + timedelta(days=1)).date()
    short_term_expiration_lte = (now + timedelta(days=60)).date()
    leap_expiration_gte = (now + timedelta(days=365)).date()
    leap_expiration_lte = (now + timedelta(days=730)).date()
    # Short-term
    short_term_req = GetOptionContractsRequest(
        underlying_symbols=[ticker],
        status=AssetStatus.ACTIVE,
        expiration_date_gte=short_term_expiration_gte,
        expiration_date_lte=short_term_expiration_lte,
        type=option_type,
        style=ExerciseStyle.AMERICAN,
        limit=100,
    )
    short_term_res = trading_client.get_option_contracts(short_term_req)
    short_term_contract = None
    max_open_interest = 0
    for contract in short_term_res.option_contracts:
        if contract.open_interest and int(contract.open_interest) > max_open_interest:
            max_open_interest = int(contract.open_interest)
            short_term_contract = contract
    # LEAP
    leap_req = GetOptionContractsRequest(
        underlying_symbols=[ticker],
        status=AssetStatus.ACTIVE,
        expiration_date_gte=leap_expiration_gte,
        expiration_date_lte=leap_expiration_lte,
        type=option_type,
        style=ExerciseStyle.AMERICAN,
        limit=100,
    )
    leap_res = trading_client.get_option_contracts(leap_req)
    leap_contract = None
    max_open_interest = 0
    for contract in leap_res.option_contracts:
        if contract.open_interest and int(contract.open_interest) > max_open_interest:
            max_open_interest = int(contract.open_interest)
            leap_contract = contract
    return {"short_term": short_term_contract.__dict__ if short_term_contract else None, "leap": leap_contract.__dict__ if leap_contract else None}

def get_corporate_actions_by_symbol(symbols, start_date=None, end_date=None) -> str:
    """
    Fetches and summarizes corporate actions for one or more symbols within a date range.
    Args:
        symbols (str or list): Single stock symbol or list of symbols
        start_date (date, optional): Start date for search range
        end_date (date, optional): End date for search range
    Returns:
        str: Formatted summary of corporate actions
    """
    if isinstance(symbols, str):
        symbols = [symbols]
    if not end_date:
        end_date = datetime.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    summary = []
    for symbol in symbols:
        try:
            filter_params = GetCorporateAnnouncementsRequest(
                ca_types=['dividend', 'merger', 'spinoff', 'split'],
                since=start_date,
                until=end_date,
                symbol=symbol
            )
            announcements = trading_client.get_corporate_announcements(filter_params)
            sorted_announcements = sorted(
                announcements,
                key=lambda x: x.declaration_date or datetime.max.date(),
                reverse=True
            )
            if sorted_announcements:
                summary.append(f"\n{len(sorted_announcements)} Corporate actions for {symbol} from {start_date} to {end_date}:")
                for action_number, announcement in enumerate(sorted_announcements, start=1):
                    if announcement:
                        action_details = f"""
Action #{action_number}:
Type: {announcement.ca_type}
Subtype: {announcement.ca_sub_type}
Companies:
- Initiating: {announcement.initiating_symbol}
- Target: {announcement.target_symbol if announcement.target_symbol else 'N/A'}
Dates:
- Declaration: {announcement.declaration_date if announcement.declaration_date else 'N/A'}
- Ex Date: {announcement.ex_date if announcement.ex_date else 'N/A'}
- Record: {announcement.record_date if announcement.record_date else 'N/A'}
- Payable: {announcement.payable_date if announcement.payable_date else 'N/A'}
Financial Details:
- Cash Amount per Share: ${format(float(announcement.cash), '.4f') if announcement.cash else 'N/A'}
- Rate Change: {format(float(announcement.new_rate), '.2f') if announcement.new_rate else 'N/A'}/{format(float(announcement.old_rate), '.2f') if announcement.old_rate else 'N/A'}
  ({format((float(announcement.new_rate)/float(announcement.old_rate) - 1)*100, '.2f') if announcement.new_rate and announcement.old_rate else 0}% change)
"""
                        summary.append(action_details)
            else:
                summary.append(f"\nNo corporate actions found for {symbol} from {start_date} to {end_date}")
        except Exception as e:
            summary.append(f"\nError fetching corporate actions for {symbol}: {e}")
    return "\n".join(summary)

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI) for a price series.
    Args:
        prices (pd.Series): Series of prices.
        period (int): RSI period.
    Returns:
        pd.Series: RSI values.
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates the Average True Range (ATR) for a DataFrame of OHLC data.
    Args:
        df (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns.
        period (int): ATR period.
    Returns:
        pd.Series: ATR values.
    """
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def get_historical_data(symbol: str) -> Optional[pd.DataFrame]:
    """
    Gets historical daily bar data for a symbol and adds technical indicators.
    Args:
        symbol (str): Stock symbol.
    Returns:
        pd.DataFrame: DataFrame with historical data and indicators.
    """
    end = datetime.now()
    start = end - timedelta(days=30)
    bars_request = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        adjustment='raw'
    )
    bars_data = data_client.get_stock_bars(bars_request)
    if not bars_data or not hasattr(bars_data, 'df'):
        return None
    df = bars_data.df
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['RSI'] = calculate_rsi(df['close'])
    df['ATR'] = calculate_atr(df)
    return df

def calculate_volatility(symbol: str) -> float:
    """
    Calculates annualized volatility for a symbol using historical data.
    Args:
        symbol (str): Stock symbol.
    Returns:
        float: Annualized volatility.
    """
    df = get_historical_data(symbol)
    if df is None:
        return 0.0
    returns = df['close'].pct_change()
    historical_vol = returns.std() * np.sqrt(252)
    atr = df['ATR'].iloc[-1]
    current_price = df['close'].iloc[-1]
    atr_vol = (atr / current_price) * np.sqrt(252)
    return 0.7 * historical_vol + 0.3 * atr_vol 