from pydantic import BaseModel


class PortfolioStats(BaseModel):
    total_records: int = 0
    unique_instruments: int = 0
    portfolios: int = 0
    sectors: int = 0
    total_aum: float = 0.0
    total_invested: float = 0.0
    total_unrealized_pnl: float = 0.0
    total_realized_pnl: float = 0.0
    avg_unrealized_pnl: float = 0.0
