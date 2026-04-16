"""Tests for InsiderProvider calculations."""

import pytest
from datetime import datetime, timedelta
from src.infrastructure.data_providers.insider_provider import InsiderProvider, InsiderTransaction


class TestInsiderProvider:
    """Test insider transaction sentiment calculations."""

    @pytest.fixture
    def provider(self):
        return InsiderProvider()

    @pytest.fixture
    def sample_transactions(self):
        """Mixed buy/sell transactions."""
        today = datetime.now()
        return [
            InsiderTransaction(
                name="John Doe",
                position="CEO",
                transaction_type="P",
                shares=1000,
                price=100.0,
                value=100000,
                date=(today - timedelta(days=30)).strftime("%Y-%m-%d"),
                is_10b5_plan=False,
            ),
            InsiderTransaction(
                name="Jane Smith",
                position="CFO",
                transaction_type="P",
                shares=500,
                price=100.0,
                value=50000,
                date=(today - timedelta(days=60)).strftime("%Y-%m-%d"),
                is_10b5_plan=False,
            ),
            InsiderTransaction(
                name="Bob Brown",
                position="Director",
                transaction_type="S",
                shares=800,
                price=110.0,
                value=88000,
                date=(today - timedelta(days=90)).strftime("%Y-%m-%d"),
                is_10b5_plan=False,
            ),
        ]

    @pytest.fixture
    def all_buys(self):
        """All buy transactions."""
        return [
            InsiderTransaction(
                name="John Doe",
                position="CEO",
                transaction_type="P",
                shares=1000,
                price=100.0,
                value=100000,
                date="2024-01-15",
                is_10b5_plan=False,
            ),
            InsiderTransaction(
                name="Jane Smith",
                position="CFO",
                transaction_type="P",
                shares=500,
                price=100.0,
                value=50000,
                date="2024-02-20",
                is_10b5_plan=False,
            ),
        ]

    @pytest.fixture
    def all_sells(self):
        """All sell transactions."""
        return [
            InsiderTransaction(
                name="Bob Brown",
                position="Director",
                transaction_type="S",
                shares=800,
                price=110.0,
                value=88000,
                date="2024-03-10",
                is_10b5_plan=False,
            ),
            InsiderTransaction(
                name="Alice Green",
                position="Officer",
                transaction_type="S",
                shares=300,
                price=105.0,
                value=31500,
                date="2024-04-05",
                is_10b5_plan=False,
            ),
        ]

    def test_compute_net_sentiment_mixed(self, provider, sample_transactions):
        """(Buys - Sells) / Total with mixed transactions."""
        result = provider.compute_net_sentiment(sample_transactions)
        assert result is not None
        assert 0 < result < 1

    def test_compute_net_sentiment_all_buys(self, provider, all_buys):
        """All buys: +1.0."""
        result = provider.compute_net_sentiment(all_buys)
        assert result == 1.0

    def test_compute_net_sentiment_all_sells(self, provider, all_sells):
        """All sells: -1.0."""
        result = provider.compute_net_sentiment(all_sells)
        assert result == -1.0

    def test_compute_net_sentiment_empty(self, provider):
        """Empty list: None."""
        result = provider.compute_net_sentiment([])
        assert result is None

    def test_compute_net_sentiment_filters_10b5(self, provider):
        """10b5-1 plan transactions are filtered out."""
        transactions = [
            InsiderTransaction(
                name="John Doe",
                position="CEO",
                transaction_type="S",
                shares=1000,
                price=100.0,
                value=100000,
                date="2024-01-15",
                is_10b5_plan=True,
            ),
            InsiderTransaction(
                name="Jane Smith",
                position="CFO",
                transaction_type="P",
                shares=500,
                price=100.0,
                value=50000,
                date="2024-02-20",
                is_10b5_plan=False,
            ),
        ]
        result = provider.compute_net_sentiment(transactions)
        assert result == 1.0

    def test_compute_net_buy_value(self, provider, sample_transactions):
        """Net dollar value over trailing months."""
        result = provider.compute_net_buy_value(sample_transactions, months=6)
        assert result is not None
        assert result > 0

    def test_compute_net_buy_value_empty(self, provider):
        """Empty list: None."""
        result = provider.compute_net_buy_value([])
        assert result is None

    def test_normalize_position_ceo(self, provider):
        """CEO title normalization."""
        assert provider._normalize_position("Chief Executive Officer") == "CEO"
        assert provider._normalize_position("CEO") == "CEO"

    def test_normalize_position_cfo(self, provider):
        """CFO title normalization."""
        assert provider._normalize_position("Chief Financial Officer") == "CFO"
        assert provider._normalize_position("CFO") == "CFO"

    def test_normalize_position_director(self, provider):
        """Director title normalization."""
        assert provider._normalize_position("Board Director") == "Director"
        assert provider._normalize_position("Director") == "Director"

    def test_normalize_position_unknown(self, provider):
        """Unknown role defaults to 'Insider'."""
        assert provider._normalize_position("Some Unknown Role") == "Insider"
