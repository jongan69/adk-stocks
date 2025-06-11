from .research import get_stock_price
from .trading import get_account_value
from .trading import calculate_volatility

def check_position_size(symbol, qty, max_pct=0.1, portfolio_value=None):
    """Rejects trades that would exceed max_pct of portfolio value."""
    price = get_stock_price(symbol)
    account_value = get_account_value() if portfolio_value is None else portfolio_value
    if (price * qty) > (max_pct * account_value):
        return False, f"Trade exceeds {max_pct*100}% of portfolio value."
    return True, "Trade within risk limits."

def check_volatility(symbol, max_vol=0.05):
    """Rejects trades if volatility is too high."""
    vol = calculate_volatility(symbol)
    if vol > max_vol:
        return False, f"Volatility {vol:.2%} exceeds max allowed {max_vol:.2%}."
    return True, "Volatility within limits." 