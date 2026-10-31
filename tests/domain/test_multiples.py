"""تست‌های واحد ارزش‌گذاری نسبی با ضریب همتایان.

اجرا از ریشه پروژه:
    python3 -m unittest discover -s tests -t . -v
"""

import unittest
from dataclasses import FrozenInstanceError

from stock_valuation.domain.dcf import dcf_valuation
from stock_valuation.domain.errors import CalculationError, ValidationError
from stock_valuation.domain.multiples import (
    ENTERPRISE_MULTIPLE_KINDS,
    ImpliedValuation,
    MultipleKind,
    PeerMultiple,
    implied_valuation,
    peer_statistics,
)
from tests.domain._fixtures import _reference_dcf_projections


def _peers(*values):
    """ساخت همتایان نام‌دار با ضریب‌های داده‌شده به همان ترتیب"""
    return [
        PeerMultiple(name=f"همتا{index}", value=value)
        for index, value in enumerate(values)
    ]


class TestPeerStatistics(unittest.TestCase):
    """آماره‌های همتایان، حذف ضریب غیرمثبت و اعتبارسنجی ورودی"""

    def test_hand_computed_quartiles_odd_count(self):
        # [10, 20, 30]: Q1 = 15، میانه = 20، Q3 = 25
        stats = peer_statistics(_peers(10.0, 20.0, 30.0))
        self.assertEqual(stats.used_count, 3)
        self.assertEqual(stats.excluded_count, 0)
        self.assertEqual(stats.excluded_names, [])
        self.assertEqual(stats.q1, 15.0)
        self.assertEqual(stats.median, 20.0)
        self.assertEqual(stats.q3, 25.0)
        self.assertEqual(stats.mean, 20.0)
        self.assertEqual(stats.min, 10.0)
        self.assertEqual(stats.max, 30.0)

    def test_hand_computed_quartiles_even_count(self):
        # [10, 20, 30, 40]: Q1 = 17.5، میانه = 25، Q3 = 32.5
        stats = peer_statistics(_peers(10.0, 20.0, 30.0, 40.0))
        self.assertEqual(stats.used_count, 4)
        self.assertEqual(stats.q1, 17.5)
        self.assertEqual(stats.median, 25.0)
        self.assertEqual(stats.q3, 32.5)
        self.assertEqual(stats.mean, 25.0)
        self.assertEqual(stats.min, 10.0)
        self.assertEqual(stats.max, 40.0)

    def test_input_order_does_not_change_statistics(self):
        ordered = peer_statistics(_peers(10.0, 20.0, 30.0, 40.0))
        shuffled = peer_statistics(_peers(30.0, 10.0, 40.0, 20.0))
        self.assertEqual(ordered, shuffled)

    def test_non_positive_peers_excluded_in_input_order(self):
        peers = [
            PeerMultiple("زیان‌ده", -5.0),
            PeerMultiple("صفر", 0.0),
            PeerMultiple("الف", 12.0),
            PeerMultiple("ب", 15.0),
            PeerMultiple("ج", 18.0),
        ]
        stats = peer_statistics(peers)
        self.assertEqual(stats.used_count, 3)
        self.assertEqual(stats.excluded_count, 2)
        self.assertEqual(stats.excluded_names, ["زیان‌ده", "صفر"])
        self.assertEqual(stats.q1, 13.5)
        self.assertEqual(stats.median, 15.0)
        self.assertEqual(stats.q3, 16.5)
        self.assertEqual(stats.mean, 15.0)
        self.assertEqual(stats.min, 12.0)
        self.assertEqual(stats.max, 18.0)

    def test_too_few_valid_peers_rejected(self):
        for peers in ([], _peers(10.0, 20.0), _peers(10.0, -5.0, 0.0)):
            with self.subTest(peers=[peer.value for peer in peers]):
                with self.assertRaises(ValidationError):
                    peer_statistics(peers)

    def test_blank_name_rejected(self):
        for name in ("", "   "):
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    peer_statistics(
                        [
                            PeerMultiple(name, 10.0),
                            PeerMultiple("الف", 20.0),
                            PeerMultiple("ب", 30.0),
                        ]
                    )

    def test_blank_name_rejected_even_when_excluded(self):
        # نام‌ها پیش از حذف ضریب غیرمثبت بررسی می‌شوند
        with self.assertRaises(ValidationError):
            peer_statistics(
                [
                    PeerMultiple("  ", -1.0),
                    PeerMultiple("الف", 20.0),
                    PeerMultiple("ب", 30.0),
                ]
            )

    def test_duplicate_name_rejected(self):
        for names in (("الف", "الف"), ("الف", " الف ")):
            with self.subTest(names=names):
                with self.assertRaises(ValidationError):
                    peer_statistics(
                        [
                            PeerMultiple(names[0], 10.0),
                            PeerMultiple(names[1], 20.0),
                            PeerMultiple("ب", 30.0),
                        ]
                    )

    def test_non_finite_multiple_rejected(self):
        # حتی ‎-inf که در حالت عادی حذف می‌شد، نامتناهی است و خطا می‌دهد
        for bad in (float("inf"), -float("inf"), float("nan")):
            with self.subTest(value=bad):
                with self.assertRaises(ValidationError):
                    peer_statistics(
                        [
                            PeerMultiple("الف", bad),
                            PeerMultiple("ب", 20.0),
                            PeerMultiple("ج", 30.0),
                        ]
                    )

    def test_non_numeric_multiple_rejected(self):
        for bad in ("15", None, True):
            with self.subTest(value=bad):
                with self.assertRaises(ValidationError):
                    peer_statistics(
                        [
                            PeerMultiple("الف", bad),
                            PeerMultiple("ب", 20.0),
                            PeerMultiple("ج", 30.0),
                        ]
                    )

    def test_non_peer_objects_rejected(self):
        for peers in (None, "abc", [("الف", 10.0)]):
            with self.subTest(peers=peers):
                with self.assertRaises(ValidationError):
                    peer_statistics(peers)

    def test_input_not_mutated_and_result_frozen(self):
        peers = _peers(30.0, 10.0, 20.0)
        snapshot = [(peer.name, peer.value) for peer in peers]
        stats = peer_statistics(peers)
        self.assertEqual([(peer.name, peer.value) for peer in peers], snapshot)
        with self.assertRaises(FrozenInstanceError):
            stats.median = 0.0  # type: ignore[misc]

    def test_deterministic(self):
        peers = _peers(10.0, 20.0, 30.0, 40.0)
        self.assertEqual(peer_statistics(peers), peer_statistics(peers))

    def test_overflowing_mean_is_calculation_error(self):
        # مجموع سه مقدار 1e308 به inf سرریز می‌کند؛ نتیجه نامعتبر است
        with self.assertRaises(CalculationError):
            peer_statistics(_peers(1e308, 1e308, 1e308))


class TestImpliedValuation(unittest.TestCase):
    """ارزش تلویحی برای هر پنج نوع ضریب و قرارداد خطای آن"""

    @staticmethod
    def _symmetric_peers():
        """همتایان با Q1 = 17.5، میانه و میانگین = 25 و Q3 = 32.5"""
        return _peers(10.0, 20.0, 30.0, 40.0)

    def test_multiple_kind_values_and_enterprise_set(self):
        self.assertEqual(
            [kind.value for kind in MultipleKind],
            ["pe", "pb", "ps", "ev_ebitda", "ev_sales"],
        )
        self.assertEqual(
            ENTERPRISE_MULTIPLE_KINDS,
            {MultipleKind.EV_EBITDA, MultipleKind.EV_SALES},
        )

    def test_pe_worked_example(self):
        result = implied_valuation(
            MultipleKind.PE, 100.0, 10.0, self._symmetric_peers()
        )
        self.assertIs(result.kind, MultipleKind.PE)
        self.assertEqual(result.metric, 100.0)
        self.assertEqual(result.low.multiple, 17.5)
        self.assertEqual(result.low.implied_equity_value, 1750.0)
        self.assertEqual(result.low.value_per_share, 175.0)
        self.assertIsNone(result.low.implied_enterprise_value)
        self.assertEqual(result.mid.multiple, 25.0)
        self.assertEqual(result.mid.implied_equity_value, 2500.0)
        self.assertEqual(result.mid.value_per_share, 250.0)
        self.assertEqual(result.high.multiple, 32.5)
        self.assertEqual(result.high.implied_equity_value, 3250.0)
        self.assertEqual(result.high.value_per_share, 325.0)
        self.assertEqual(result.mean.value_per_share, 250.0)

    def test_pb_worked_example(self):
        result = implied_valuation(
            "pb", 800.0, 10.0, self._symmetric_peers()
        )
        self.assertIs(result.kind, MultipleKind.PB)
        self.assertEqual(result.low.implied_equity_value, 14000.0)
        self.assertEqual(result.mid.implied_equity_value, 20000.0)
        self.assertEqual(result.high.implied_equity_value, 26000.0)
        self.assertEqual(
            (
                result.low.value_per_share,
                result.mid.value_per_share,
                result.high.value_per_share,
            ),
            (1400.0, 2000.0, 2600.0),
        )

    def test_ps_worked_example(self):
        result = implied_valuation(
            MultipleKind.PS, 2000.0, 10.0, self._symmetric_peers()
        )
        self.assertIs(result.kind, MultipleKind.PS)
        self.assertEqual(result.low.implied_equity_value, 35000.0)
        self.assertEqual(result.mid.implied_equity_value, 50000.0)
        self.assertEqual(result.high.implied_equity_value, 65000.0)
        self.assertEqual(
            (
                result.low.value_per_share,
                result.mid.value_per_share,
                result.high.value_per_share,
            ),
            (3500.0, 5000.0, 6500.0),
        )

    def test_ev_ebitda_worked_example(self):
        result = implied_valuation(
            MultipleKind.EV_EBITDA,
            500.0,
            10.0,
            self._symmetric_peers(),
            cash=100.0,
            debt=300.0,
            minority_interest=50.0,
            preferred_equity=50.0,
        )
        self.assertIs(result.kind, MultipleKind.EV_EBITDA)
        # Q1: EV = 17.5 × 500 = 8750 ← 8750 + 100 − 300 − 50 − 50 = 8450
        self.assertEqual(result.low.implied_enterprise_value, 8750.0)
        self.assertEqual(result.low.implied_equity_value, 8450.0)
        self.assertEqual(result.low.value_per_share, 845.0)
        # میانه: EV = 25 × 500 = 12500 ← 12200 / 10 = 1220
        self.assertEqual(result.mid.implied_enterprise_value, 12500.0)
        self.assertEqual(result.mid.implied_equity_value, 12200.0)
        self.assertEqual(result.mid.value_per_share, 1220.0)
        # Q3: EV = 32.5 × 500 = 16250 ← 15950 / 10 = 1595
        self.assertEqual(result.high.implied_enterprise_value, 16250.0)
        self.assertEqual(result.high.implied_equity_value, 15950.0)
        self.assertEqual(result.high.value_per_share, 1595.0)
        self.assertEqual(result.mean.value_per_share, 1220.0)

    def test_ev_sales_worked_example(self):
        result = implied_valuation(
            MultipleKind.EV_SALES,
            2000.0,
            10.0,
            self._symmetric_peers(),
            cash=100.0,
            debt=300.0,
            minority_interest=50.0,
            preferred_equity=50.0,
        )
        self.assertIs(result.kind, MultipleKind.EV_SALES)
        # Q1: EV = 17.5 × 2000 = 35000 ← 34700 / 10 = 3470
        self.assertEqual(result.low.implied_enterprise_value, 35000.0)
        self.assertEqual(result.low.implied_equity_value, 34700.0)
        self.assertEqual(result.low.value_per_share, 3470.0)
        # میانه: EV = 25 × 2000 = 50000 ← 49700 / 10 = 4970
        self.assertEqual(result.mid.implied_enterprise_value, 50000.0)
        self.assertEqual(result.mid.implied_equity_value, 49700.0)
        self.assertEqual(result.mid.value_per_share, 4970.0)
        # Q3: EV = 32.5 × 2000 = 65000 ← 64700 / 10 = 6470
        self.assertEqual(result.high.implied_enterprise_value, 65000.0)
        self.assertEqual(result.high.implied_equity_value, 64700.0)
        self.assertEqual(result.high.value_per_share, 6470.0)

    def test_enterprise_kinds_match_dcf_bridge_bit_for_bit(self):
        # ضریب ۱ یعنی ارزش بنگاه تلویحی عیناً همان EV مدل DCF است؛
        # بنابراین حقوق صاحبان سهام و ارزش هر سهم باید بیت‌به‌بیت برابر
        # خروجی dcf_valuation باشد (منبع واحد حقیقت: domain.bridge).
        dcf = dcf_valuation(
            _reference_dcf_projections(),
            0.10,
            0.02,
            5.0,
            0.25,
            cash=50.0,
            debt=200.0,
            minority_interest=30.0,
            preferred_equity=20.0,
        )
        peers = [
            PeerMultiple("الف", 1.0),
            PeerMultiple("ب", 1.0),
            PeerMultiple("ج", 1.0),
        ]
        for kind in (MultipleKind.EV_EBITDA, MultipleKind.EV_SALES):
            with self.subTest(kind=kind):
                result = implied_valuation(
                    kind,
                    dcf.enterprise_value,
                    5.0,
                    peers,
                    cash=50.0,
                    debt=200.0,
                    minority_interest=30.0,
                    preferred_equity=20.0,
                )
                for case in (result.low, result.mid, result.high, result.mean):
                    self.assertEqual(
                        case.implied_enterprise_value, dcf.enterprise_value
                    )
                    self.assertEqual(case.implied_equity_value, dcf.equity_value)
                    self.assertEqual(case.value_per_share, dcf.value_per_share)

    def test_mean_case_can_differ_from_median(self):
        peers = _peers(10.0, 20.0, 30.0, 100.0)
        result = implied_valuation(MultipleKind.PE, 100.0, 10.0, peers)
        self.assertEqual(result.mid.multiple, 25.0)
        self.assertEqual(result.mid.value_per_share, 250.0)
        self.assertEqual(result.mean.multiple, 40.0)
        self.assertEqual(result.mean.value_per_share, 400.0)

    def test_negative_implied_equity_not_clamped(self):
        peers = [
            PeerMultiple("الف", 1.0),
            PeerMultiple("ب", 1.0),
            PeerMultiple("ج", 1.0),
        ]
        result = implied_valuation(
            MultipleKind.EV_EBITDA, 100.0, 2.0, peers, debt=500.0
        )
        self.assertEqual(result.mid.implied_enterprise_value, 100.0)
        self.assertEqual(result.mid.implied_equity_value, -400.0)
        self.assertEqual(result.mid.value_per_share, -200.0)

    def test_invalid_kind_rejected(self):
        for kind in ("peg", "", None, 3):
            with self.subTest(kind=kind):
                with self.assertRaises(ValidationError):
                    implied_valuation(
                        kind, 100.0, 10.0, self._symmetric_peers()
                    )

    def test_invalid_metric_rejected(self):
        for metric in (0.0, -100.0, float("nan"), float("inf"), "100", True):
            with self.subTest(metric=metric):
                with self.assertRaises(ValidationError):
                    implied_valuation(
                        MultipleKind.PE, metric, 10.0, self._symmetric_peers()
                    )

    def test_invalid_shares_rejected(self):
        for shares in (0.0, -5.0, float("inf")):
            with self.subTest(shares=shares):
                with self.assertRaises(ValidationError):
                    implied_valuation(
                        MultipleKind.PE, 100.0, shares, self._symmetric_peers()
                    )

    def test_peer_validation_propagates(self):
        with self.assertRaises(ValidationError):
            implied_valuation(MultipleKind.PE, 100.0, 10.0, _peers(10.0, 20.0))

    def test_negative_balance_sheet_rejected_for_enterprise_kinds(self):
        with self.assertRaises(ValidationError):
            implied_valuation(
                MultipleKind.EV_SALES,
                2000.0,
                10.0,
                self._symmetric_peers(),
                debt=-1.0,
            )

    def test_overflowing_implied_value_is_calculation_error(self):
        # 10 × 1e308 به inf سرریز می‌کند؛ نتیجه نامعتبر است
        with self.assertRaises(CalculationError):
            implied_valuation(
                MultipleKind.PE, 1e308, 1.0, _peers(10.0, 10.0, 10.0)
            )

    def test_deterministic_frozen_and_inputs_unchanged(self):
        peers = self._symmetric_peers()
        snapshot = [(peer.name, peer.value) for peer in peers]
        first = implied_valuation(
            MultipleKind.EV_EBITDA,
            500.0,
            10.0,
            peers,
            cash=100.0,
            debt=300.0,
        )
        second = implied_valuation(
            MultipleKind.EV_EBITDA,
            500.0,
            10.0,
            peers,
            cash=100.0,
            debt=300.0,
        )
        self.assertEqual(first, second)
        self.assertIsInstance(first, ImpliedValuation)
        self.assertEqual([(peer.name, peer.value) for peer in peers], snapshot)
        with self.assertRaises(FrozenInstanceError):
            first.metric = 0.0  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
