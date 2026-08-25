"""
Unit tests for Spend Guard:
1. Allow generation when user is under budget
2. Block generation when estimated cost would exceed monthly spend cap
3. Remaining budget arithmetic
"""
import pytest
from unittest.mock import MagicMock, patch
from services.spend_guard import SpendGuard, SpendCheckResult


@pytest.mark.asyncio
async def test_spend_guard_allows_under_cap():
    spend_guard = SpendGuard()

    # Mock admin client returning $5 spend and $20 cap
    with patch("services.spend_guard.get_admin_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock profile query
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "monthly_spend_cap_usd": 20.00
        }
        # Mock projects query
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "proj-1"}
        ]
        # Mock routing_logs sum query
        mock_client.table.return_value.select.return_value.in_.return_value.gte.return_value.execute.return_value.data = [
            {"cost_usd": 2.50},
            {"cost_usd": 2.50}
        ]

        res = await spend_guard.check_and_reserve(user_id="test-user", estimated_cost_usd=0.08)
        assert res.allowed is True
        assert res.current_spend_usd == 5.00
        assert res.monthly_spend_cap_usd == 20.00
        assert res.remaining_usd == 15.00


@pytest.mark.asyncio
async def test_spend_guard_blocks_over_cap():
    spend_guard = SpendGuard()

    with patch("services.spend_guard.get_admin_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "monthly_spend_cap_usd": 5.00
        }
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "proj-1"}
        ]
        mock_client.table.return_value.select.return_value.in_.return_value.gte.return_value.execute.return_value.data = [
            {"cost_usd": 4.95}
        ]

        # Requesting $0.10 when only $0.05 left under $5.00 cap
        res = await spend_guard.check_and_reserve(user_id="test-user", estimated_cost_usd=0.10)
        assert res.allowed is False
        assert "Generation blocked" in res.error_message
