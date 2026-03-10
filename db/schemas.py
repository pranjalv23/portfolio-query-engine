from pydantic import BaseModel


class Holding(BaseModel):
    id: int
    client_id: str
    account_id: str
    instrument_name: str
    ticker: str
    asset_type: str
    sector: str
    quantity: float
    average_buy_price: float
    current_price: float
    invested_value: float
    current_value: float
    unrealized_pnl: float
    realized_pnl: float
    trade_date: str
    holding_date: str
    portfolio_name: str
