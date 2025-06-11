import pandas as pd
import yfinance as yf
import numpy as np
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.valuation import Valuation
from finvizfinance.screener.financial import Financial

def replace_nan_in_dict(d):
    if isinstance(d, dict):
        return {k: replace_nan_in_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [replace_nan_in_dict(i) for i in d]
    elif isinstance(d, float) and (pd.isna(d) or d != d):
        return None
    else:
        return d

# --- Finviz Tools ---
VALID_OVERVIEW_FILTERS = [
    'Exchange', 'Index', 'Sector', 'Industry', 'Country', 'Market Cap.', 'P/E', 'Forward P/E', 'PEG', 'P/S', 'P/B',
    'Price/Cash', 'Price/Free Cash Flow', 'EPS growththis year', 'EPS growthnext year', 'EPS growthpast 5 years',
    'EPS growthnext 5 years', 'Sales growthpast 5 years', 'EPS growthqtr over qtr', 'Sales growthqtr over qtr',
    'Dividend Yield', 'Return on Assets', 'Return on Equity', 'Return on Investment', 'Current Ratio', 'Quick Ratio',
    'LT Debt/Equity', 'Debt/Equity', 'Gross Margin', 'Operating Margin', 'Net Profit Margin', 'Payout Ratio',
    'InsiderOwnership', 'InsiderTransactions', 'InstitutionalOwnership', 'InstitutionalTransactions', 'Float Short',
    'Analyst Recom.', 'Option/Short', 'Earnings Date', 'Performance', 'Performance 2', 'Volatility', 'RSI (14)', 'Gap',
    '20-Day Simple Moving Average', '50-Day Simple Moving Average', '200-Day Simple Moving Average', 'Change',
    'Change from Open', '20-Day High/Low', '50-Day High/Low', '52-Week High/Low', 'Pattern', 'Candlestick', 'Beta',
    'Average True Range', 'Average Volume', 'Relative Volume', 'Current Volume', 'Price', 'Target Price', 'IPO Date',
    'Shares Outstanding', 'Float'
]

def get_screener_overview_tool(filters: dict) -> list:
    """
    Returns a stock screener overview using Finviz with the specified filters.
    Args:
        filters (dict): Dictionary of screener filters (e.g., {'Sector': 'Technology'}).
            Valid filters: ['Exchange', 'Index', 'Sector', 'Industry', 'Country', 'Market Cap.', 'P/E', 'Forward P/E', 'PEG', 'P/S', 'P/B',
            'Price/Cash', 'Price/Free Cash Flow', 'EPS growththis year', 'EPS growthnext year', 'EPS growthpast 5 years',
            'EPS growthnext 5 years', 'Sales growthpast 5 years', 'EPS growthqtr over qtr', 'Sales growthqtr over qtr',
            'Dividend Yield', 'Return on Assets', 'Return on Equity', 'Return on Investment', 'Current Ratio', 'Quick Ratio',
            'LT Debt/Equity', 'Debt/Equity', 'Gross Margin', 'Operating Margin', 'Net Profit Margin', 'Payout Ratio',
            'InsiderOwnership', 'InsiderTransactions', 'InstitutionalOwnership', 'InstitutionalTransactions', 'Float Short',
            'Analyst Recom.', 'Option/Short', 'Earnings Date', 'Performance', 'Performance 2', 'Volatility', 'RSI (14)', 'Gap',
            '20-Day Simple Moving Average', '50-Day Simple Moving Average', '200-Day Simple Moving Average', 'Change',
            'Change from Open', '20-Day High/Low', '50-Day High/Low', '52-Week High/Low', 'Pattern', 'Candlestick', 'Beta',
            'Average True Range', 'Average Volume', 'Relative Volume', 'Current Volume', 'Price', 'Target Price', 'IPO Date',
            'Shares Outstanding', 'Float']
    Returns:
        list: List of stock overview records.
    Raises:
        ValueError: If any filter is not valid.
    """
    for f in filters:
        if f not in VALID_OVERVIEW_FILTERS:
            raise ValueError(f"Invalid filter '{f}'. Valid filters: {VALID_OVERVIEW_FILTERS}")
    overview = Overview()
    overview.set_filter(filters_dict=filters)
    df = overview.screener_view()
    df = df.where(pd.notnull(df), None)
    print(f"[get_screener_overview_tool] Filters: {filters}")
    print(f"[get_screener_overview_tool] Found {len(df)} stocks. First 3 rows:\n{df.head(3)}")
    records = df.to_dict('records')
    records = replace_nan_in_dict(records)
    return records

def get_screener_valuation_tool(filters: dict) -> list:
    """
    Returns stock screener valuation metrics using Finviz with the specified filters.
    Args:
        filters (dict): Dictionary of screener filters.
    Returns:
        list: List of valuation records.
    """
    valuation = Valuation()
    valuation.set_filter(filters_dict=filters)
    df = valuation.screener_view()
    df = df.where(pd.notnull(df), None)
    print(f"[get_screener_valuation_tool] Filters: {filters}")
    print(f"[get_screener_valuation_tool] Found {len(df)} stocks. First 3 rows:\n{df.head(3)}")
    records = df.to_dict('records')
    records = replace_nan_in_dict(records)
    return records

def get_screener_financial_tool(filters: dict) -> list:
    """
    Returns stock screener financial metrics using Finviz with the specified filters.
    Args:
        filters (dict): Dictionary of screener filters.
    Returns:
        list: List of financial records.
    """
    financial = Financial()
    financial.set_filter(filters_dict=filters)
    df = financial.screener_view()
    df = df.where(pd.notnull(df), None)
    print(f"[get_screener_financial_tool] Filters: {filters}")
    print(f"[get_screener_financial_tool] Found {len(df)} stocks. First 3 rows:\n{df.head(3)}")
    records = df.to_dict('records')
    records = replace_nan_in_dict(records)
    return records

def get_highest_volume_tool(limit: int = 100) -> list:
    """
    Returns a list of stocks with the highest trading volume using Finviz.
    Args:
        limit (int): Number of stocks to return.
    Returns:
        list: List of stocks with the highest volume.
    """
    screener = Overview()
    pages_needed = (limit + 19) // 20
    df = pd.DataFrame()
    for page in range(1, pages_needed + 1):
        page_df = screener.screener_view(
            order='Volume',
            verbose=1,
            select_page=page,
            ascend=False
        )
        df = pd.concat([df, page_df], ignore_index=True)
        if len(df) >= limit:
            break
    if df['Volume'].dtype == object:
        df['Volume'] = df['Volume'].str.replace(',', '').astype(int)
    df = df.sort_values(by='Volume', ascending=False).head(limit)
    df = df.where(pd.notnull(df), None)
    print(f"[get_highest_volume_tool] Returning top {limit} by volume. Found {len(df)} stocks. First 3 rows:\n{df.head(3)}")
    records = df.to_dict('records')
    records = replace_nan_in_dict(records)
    return records

# --- Yahoo Finance Tools ---
def get_stock_price(ticker: str) -> float:
    """
    Returns the latest closing price for the given stock ticker using Yahoo Finance.
    Args:
        ticker (str): The stock ticker symbol (e.g., 'AAPL').
    Returns:
        float: The latest closing price.
    """
    data = yf.Ticker(ticker)
    closes = data.history(period='1d')['Close']
    price = float(closes.iloc[-1])
    print(f"[get_stock_price] {ticker}: {price}")
    return price

def series_to_serializable(val):
    if isinstance(val, pd.Series):
        if len(val) == 1:
            return val.iloc[0]
        return val.dropna().tolist()
    return val

def get_all_fundamental_metrics(ticker: str) -> dict:
    """
    Returns a dictionary of fundamental metrics for the given stock ticker using Yahoo Finance.
    Args:
        ticker (str): The stock ticker symbol.
    Returns:
        dict: Dictionary of fundamental metrics (revenue, net income, eps, etc.).
    """
    data = yf.Ticker(ticker)
    metrics = {}
    try:
        income_stmt = data.financials
        balance_sheet = data.balance_sheet
        cash_flow_stmt = data.cash_flow
        metrics['revenue'] = income_stmt.loc['Total Revenue'] if 'Total Revenue' in income_stmt.index else None
        metrics['net_income'] = income_stmt.loc['Net Income'] if 'Net Income' in income_stmt.index else None
        metrics['eps'] = data.info.get('trailingEps', 0)
        metrics['gross_profit'] = income_stmt.loc['Gross Profit'] if 'Gross Profit' in income_stmt.index else None
        metrics['operating_income'] = income_stmt.loc['Operating Income'] if 'Operating Income' in income_stmt.index else None
        metrics['operating_cash_flow'] = cash_flow_stmt.loc['Operating Cash Flow'] if 'Operating Cash Flow' in cash_flow_stmt.index else None
        metrics['capital_expenditure'] = cash_flow_stmt.loc['Capital Expenditure'] if 'Capital Expenditure' in cash_flow_stmt.index else None
        metrics['total_assets'] = balance_sheet.loc['Total Assets'] if 'Total Assets' in balance_sheet.index else None
        metrics['total_liabilities'] = balance_sheet.loc['Total Liab'] if 'Total Liab' in balance_sheet.index else None
        metrics['current_assets'] = balance_sheet.loc['Total Current Assets'] if 'Total Current Assets' in balance_sheet.index else None
        metrics['current_liabilities'] = balance_sheet.loc['Total Current Liabilities'] if 'Total Current Liabilities' in balance_sheet.index else None
        metrics['cash'] = balance_sheet.loc['Cash'] if 'Cash' in balance_sheet.index else None
        metrics['inventory'] = balance_sheet.loc['Inventory'] if 'Inventory' in balance_sheet.index else None
        metrics['accounts_receivable'] = balance_sheet.loc['Net Receivables'] if 'Net Receivables' in balance_sheet.index else None
        metrics['accounts_payable'] = balance_sheet.loc['Accounts Payable'] if 'Accounts Payable' in balance_sheet.index else None
        metrics['shareholders_equity'] = balance_sheet.loc['Total Stockholder Equity'] if 'Total Stockholder Equity' in balance_sheet.index else None
        metrics['outstanding_shares'] = data.info.get('sharesOutstanding', 0)
        metrics['dividend_yield'] = data.info.get('dividendYield', 0) * 100 if data.info.get('dividendYield') else 0
    except Exception as e:
        metrics['error'] = str(e)
    # Convert all pandas.Series to serializable types
    metrics = {k: series_to_serializable(v) for k, v in metrics.items()}
    print(f"[get_all_fundamental_metrics] {ticker}: {metrics}")
    return metrics 