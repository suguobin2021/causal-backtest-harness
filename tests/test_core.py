from datetime import datetime, timezone
import unittest

from causal_backtest_harness import (
    Bar,
    BarCompletionPolicy,
    ExecutionPolicy,
    ExecutionViolation,
    Side,
    execute_next_bar,
)

UTC = timezone.utc


def dt(minute: int) -> datetime:
    return datetime(2026, 1, 1, 0, minute, tzinfo=UTC)


def bar(i: int, *, complete=True, open_price=100.0) -> Bar:
    return Bar(
        open_time=dt(i * 5),
        close_time=dt((i + 1) * 5),
        open=open_price,
        high=open_price + 2,
        low=open_price - 2,
        close=open_price + 1,
        complete=complete,
    )


class CoreTests(unittest.TestCase):
    def test_next_bar_execution_uses_future_open(self):
        out = execute_next_bar(
            [bar(0), bar(1, open_price=105.0)],
            signal_index=0,
            side=Side.LONG,
        )
        self.assertEqual(out.entry_time, dt(5))
        self.assertEqual(out.raw_entry_price, 105.0)

    def test_incomplete_signal_bar_fails_closed(self):
        with self.assertRaises(ExecutionViolation):
            execute_next_bar(
                [bar(0, complete=False), bar(1)],
                signal_index=0,
                side=Side.LONG,
            )

    def test_unknown_completion_fails_closed_by_default(self):
        with self.assertRaises(ExecutionViolation):
            execute_next_bar(
                [bar(0, complete=None), bar(1)],
                signal_index=0,
                side=Side.SHORT,
            )

    def test_unknown_completion_can_be_explicitly_allowed(self):
        policy = ExecutionPolicy(
            bar_completion=BarCompletionPolicy.ALLOW_UNKNOWN
        )
        out = execute_next_bar(
            [bar(0, complete=None), bar(1)],
            signal_index=0,
            side=Side.SHORT,
            policy=policy,
        )
        self.assertEqual(out.entry_time, dt(5))

    def test_same_bar_execution_cannot_be_configured(self):
        with self.assertRaises(ExecutionViolation):
            execute_next_bar(
                [bar(0), bar(1)],
                signal_index=0,
                side=Side.LONG,
                policy=ExecutionPolicy(entry_delay_bars=0),
            )

    def test_no_future_bar_fails_closed(self):
        with self.assertRaises(ExecutionViolation):
            execute_next_bar([bar(0)], signal_index=0, side=Side.LONG)

    def test_overlapping_entry_bar_is_rejected(self):
        overlapping = Bar(
            dt(4),
            dt(9),
            100,
            102,
            98,
            101,
            True,
        )
        with self.assertRaises(ExecutionViolation):
            execute_next_bar(
                [bar(0), overlapping],
                signal_index=0,
                side=Side.LONG,
            )

    def test_slippage_is_adverse_on_entry(self):
        bars = [bar(0), bar(1, open_price=100.0)]
        policy = ExecutionPolicy(slippage_bps=10)
        long_out = execute_next_bar(
            bars, signal_index=0, side=Side.LONG, policy=policy
        )
        short_out = execute_next_bar(
            bars, signal_index=0, side=Side.SHORT, policy=policy
        )
        self.assertAlmostEqual(long_out.effective_entry_price, 100.1)
        self.assertAlmostEqual(short_out.effective_entry_price, 99.9)

    def test_invalid_bar_geometry_is_rejected(self):
        bad = Bar(dt(0), dt(5), 100, 99, 98, 101, True)
        with self.assertRaises(ExecutionViolation):
            execute_next_bar(
                [bad, bar(1)],
                signal_index=0,
                side=Side.LONG,
            )


if __name__ == "__main__":
    unittest.main()
