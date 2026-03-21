"""Tests for screening filters."""

from screener.filters import apply_filters


def _make_stock(**overrides) -> dict:
    base = {
        "ticker": "TEST",
        "name": "Test Corp",
        "price": 100.0,
        "market_cap": 5_000_000_000,
        "pe_ratio": 15.0,
        "revenue_growth": 0.10,
        "avg_volume": 1_000_000,
        "recent_volume": 1_200_000,
        "sma_50": 95.0,
    }
    base.update(overrides)
    return base


def test_passes_all_defaults():
    stocks = [_make_stock()]
    assert len(apply_filters(stocks)) == 1


def test_fails_market_cap():
    stocks = [_make_stock(market_cap=500_000_000)]
    assert len(apply_filters(stocks)) == 0


def test_fails_volume():
    stocks = [_make_stock(avg_volume=100_000)]
    assert len(apply_filters(stocks)) == 0


def test_fails_pe_too_high():
    stocks = [_make_stock(pe_ratio=50)]
    assert len(apply_filters(stocks)) == 0


def test_fails_pe_too_low():
    stocks = [_make_stock(pe_ratio=3)]
    assert len(apply_filters(stocks)) == 0


def test_fails_below_sma():
    stocks = [_make_stock(price=90.0, sma_50=100.0)]
    assert len(apply_filters(stocks)) == 0


def test_passes_no_pe():
    """Stocks without P/E data should still pass (e.g., pre-revenue)."""
    stocks = [_make_stock(pe_ratio=None)]
    assert len(apply_filters(stocks)) == 1


def test_custom_criteria():
    stocks = [_make_stock(market_cap=500_000_000)]
    result = apply_filters(stocks, {"min_market_cap": 100_000_000})
    assert len(result) == 1
