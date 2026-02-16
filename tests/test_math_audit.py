from datetime import datetime

import pytest

from core.services_enhanced import EnhancedFundManager
from helpers import parse_currency


class DummyHandler:
    connected = True

    def save_all_data_enhanced(self, *args, **kwargs):
        return True


def _new_manager():
    manager = EnhancedFundManager(DummyHandler())
    manager._ensure_fund_manager_exists()
    return manager


def _setup_withdrawal_scenario():
    manager = _new_manager()
    manager.add_investor("Alice")
    investor_id = [i.id for i in manager.investors if not i.is_fund_manager][0]

    manager.process_deposit(
        investor_id, 100_000_000, 100_000_000, datetime(2025, 1, 1, 10, 0, 0)
    )
    manager.process_nav_update(120_000_000, datetime(2025, 1, 2, 10, 0, 0))
    ok, _ = manager.process_withdrawal(
        investor_id, 20_000_000, 100_000_000, datetime(2025, 1, 3, 10, 0, 0)
    )
    assert ok
    return manager, investor_id


def _is_withdraw(tx_type: str) -> bool:
    return tx_type.lower().startswith("r")


def _is_fee(tx_type: str) -> bool:
    return tx_type.lower().startswith("p")


def _is_deposit(tx_type: str) -> bool:
    return tx_type.lower().startswith("n")


def test_latest_nav_same_day_uses_full_datetime():
    manager = _new_manager()
    manager._add_transaction(0, datetime(2025, 1, 4, 15, 0, 0), "NAV Update", 0, 130_000_000, 0)
    manager._add_transaction(0, datetime(2025, 1, 4, 9, 0, 0), "NAV Update", 0, 110_000_000, 0)

    assert manager.get_latest_total_nav() == 130_000_000


def test_latest_nav_includes_zero_value():
    manager = _new_manager()
    manager._add_transaction(0, datetime(2025, 1, 1, 10, 0, 0), "NAV Update", 0, 100_000_000, 0)
    manager._add_transaction(0, datetime(2025, 1, 2, 10, 0, 0), "NAV Update", 0, 0, 0)

    assert manager.get_latest_total_nav() == 0


def test_delete_withdrawal_is_atomic_with_fee_artifacts():
    manager, investor_id = _setup_withdrawal_scenario()
    fund_manager_id = manager.get_fund_manager().id

    withdrawal_tx = max(
        [t for t in manager.transactions if t.investor_id == investor_id and _is_withdraw(t.type)],
        key=lambda t: t.id,
    )
    assert manager.delete_transaction(withdrawal_tx.id) is True

    investor_types = [t.type for t in manager.transactions if t.investor_id == investor_id]
    assert not any(_is_withdraw(tx_type) for tx_type in investor_types)
    assert not any(_is_fee(tx_type) for tx_type in investor_types)
    assert not [
        fr
        for fr in manager.fee_records
        if fr.investor_id == investor_id and fr.period.startswith("Withdrawal")
    ]

    assert manager.get_investor_units(investor_id) == pytest.approx(10_000.0, rel=1e-6)
    assert manager.get_investor_units(fund_manager_id) == pytest.approx(0.0, abs=1e-8)
    assert sum(t.cumulative_fees_paid for t in manager.get_investor_tranches(investor_id)) == pytest.approx(0.0, abs=1e-8)


def test_undo_withdrawal_handles_complex_case():
    manager, investor_id = _setup_withdrawal_scenario()
    withdrawal_tx = max(
        [t for t in manager.transactions if t.investor_id == investor_id and _is_withdraw(t.type)],
        key=lambda t: t.id,
    )

    assert manager.undo_last_transaction(withdrawal_tx.id) is True
    investor_types = [t.type for t in manager.transactions if t.investor_id == investor_id]
    assert not any(_is_withdraw(tx_type) for tx_type in investor_types)
    assert not any(_is_fee(tx_type) for tx_type in investor_types)


def test_lifetime_performance_uses_cashflow_model():
    manager, investor_id = _setup_withdrawal_scenario()
    current_nav = manager.get_latest_total_nav()
    performance = manager.get_investor_lifetime_performance(investor_id, current_nav)

    current_units = manager.get_investor_units(investor_id)
    current_price = manager.calculate_price_per_unit(current_nav)
    current_value = current_units * current_price
    cash_out = sum(
        -t.amount for t in manager.transactions if t.investor_id == investor_id and _is_withdraw(t.type) and t.amount < 0
    )
    fees_paid = sum(
        -t.amount for t in manager.transactions if t.investor_id == investor_id and _is_fee(t.type) and t.amount < 0
    )

    expected_net_profit = current_value + cash_out - 100_000_000

    assert performance["original_invested"] == pytest.approx(100_000_000, rel=1e-9)
    assert performance["total_fees_paid"] == pytest.approx(fees_paid, rel=1e-9)
    assert performance["net_profit"] == pytest.approx(expected_net_profit, rel=1e-9)
    assert performance["gross_profit"] == pytest.approx(expected_net_profit + fees_paid, rel=1e-9)


def test_parse_currency_supports_vn_formats():
    assert parse_currency("100,000,000") == 100_000_000.0
    assert parse_currency("100.000.000") == 100_000_000.0
    assert parse_currency("100 000 000") == 100_000_000.0
    assert parse_currency("100_000_000đ") == 100_000_000.0


def test_deposit_uses_inferred_pre_nav_for_unit_pricing():
    manager = _new_manager()
    manager.add_investor("Alice")
    investor_id = [i.id for i in manager.investors if not i.is_fund_manager][0]

    manager.process_deposit(
        investor_id, 100_000_000, 100_000_000, datetime(2025, 1, 1, 10, 0, 0)
    )
    manager.process_nav_update(2_000_000_000, datetime(2025, 1, 2, 10, 0, 0))

    ok, _ = manager.process_deposit(
        investor_id, 50_000_000, 2_150_000_000, datetime(2025, 1, 3, 10, 0, 0)
    )
    assert ok

    deposit_tx = max(
        [
            t
            for t in manager.transactions
            if t.investor_id == investor_id and _is_deposit(t.type) and abs(t.amount - 50_000_000) < 1
        ],
        key=lambda t: t.id,
    )

    expected_pre_nav = 2_150_000_000 - 50_000_000
    expected_price = expected_pre_nav / 10_000.0
    expected_units = 50_000_000 / expected_price

    assert deposit_tx.units_change == pytest.approx(expected_units, rel=1e-9)
    latest_tranche = max(
        [t for t in manager.get_investor_tranches(investor_id)],
        key=lambda t: t.entry_date,
    )
    assert latest_tranche.entry_nav == pytest.approx(expected_price, rel=1e-9)


def test_withdrawal_uses_inferred_pre_nav_for_unit_pricing():
    manager = _new_manager()
    manager.add_investor("Alice")
    investor_id = [i.id for i in manager.investors if not i.is_fund_manager][0]

    manager.process_deposit(
        investor_id, 100_000_000, 100_000_000, datetime(2025, 1, 1, 10, 0, 0)
    )
    manager.process_nav_update(100_000_000, datetime(2025, 1, 2, 10, 0, 0))

    ok, _ = manager.process_withdrawal(
        investor_id, 5_000_000, 105_000_000, datetime(2025, 1, 3, 10, 0, 0)
    )
    assert ok

    withdrawal_tx = max(
        [t for t in manager.transactions if t.investor_id == investor_id and _is_withdraw(t.type)],
        key=lambda t: t.id,
    )
    expected_pre_nav = 105_000_000 + 5_000_000
    expected_price = expected_pre_nav / 10_000.0
    expected_units = 5_000_000 / expected_price

    assert withdrawal_tx.nav == pytest.approx(105_000_000.0, rel=1e-12)
    assert abs(withdrawal_tx.units_change) == pytest.approx(expected_units, rel=1e-9)
