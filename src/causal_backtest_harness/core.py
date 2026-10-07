from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable


class ExecutionViolation(ValueError):
    """Raised when an execution violates the declared causal contract."""


class Side(str, Enum):
    LONG = "long"
    SHORT = "short"


class BarCompletionPolicy(str, Enum):
    REQUIRE_COMPLETE = "require_complete"
    ALLOW_UNKNOWN = "allow_unknown"


@dataclass(frozen=True)
class Bar:
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    complete: bool | None = None

    def validate(self) -> None:
        if self.close_time <= self.open_time:
            raise ExecutionViolation("bar close_time must be after open_time")
        if self.low > self.high:
            raise ExecutionViolation("bar low cannot exceed high")
        if self.high < max(self.open, self.close):
            raise ExecutionViolation("bar high cannot be below the candle body")
        if self.low > min(self.open, self.close):
            raise ExecutionViolation("bar low cannot be above the candle body")


@dataclass(frozen=True)
class ExecutionPolicy:
    bar_completion: BarCompletionPolicy = BarCompletionPolicy.REQUIRE_COMPLETE
    entry_delay_bars: int = 1
    fee_bps: float = 0.0
    slippage_bps: float = 0.0

    def validate(self) -> None:
        if self.entry_delay_bars < 1:
            raise ExecutionViolation("entry_delay_bars must be at least 1")
        if self.fee_bps < 0 or self.slippage_bps < 0:
            raise ExecutionViolation("fee_bps and slippage_bps must be non-negative")


@dataclass(frozen=True)
class ExecutionResult:
    side: Side
    signal_bar_close: datetime
    entry_time: datetime
    raw_entry_price: float
    effective_entry_price: float
    fee_bps: float
    slippage_bps: float


def execute_next_bar(
    bars: Iterable[Bar],
    *,
    signal_index: int,
    side: Side,
    policy: ExecutionPolicy | None = None,
) -> ExecutionResult:
    """Execute a signal at a strictly future bar open under an explicit causal contract."""
    policy = policy or ExecutionPolicy()
    policy.validate()
    materialized = list(bars)

    if signal_index < 0 or signal_index >= len(materialized):
        raise IndexError("signal_index out of range")

    signal_bar = materialized[signal_index]
    signal_bar.validate()

    if (
        policy.bar_completion is BarCompletionPolicy.REQUIRE_COMPLETE
        and signal_bar.complete is not True
    ):
        raise ExecutionViolation(
            "selected policy requires explicit evidence that the signal bar is complete"
        )

    entry_index = signal_index + policy.entry_delay_bars
    if entry_index >= len(materialized):
        raise ExecutionViolation("no future bar is available for causal execution")

    entry_bar = materialized[entry_index]
    entry_bar.validate()

    if entry_bar.open_time < signal_bar.close_time:
        raise ExecutionViolation("entry bar opens before the signal bar has closed")

    raw = entry_bar.open
    delta = raw * policy.slippage_bps / 10_000.0
    effective = raw + delta if side is Side.LONG else raw - delta

    return ExecutionResult(
        side=side,
        signal_bar_close=signal_bar.close_time,
        entry_time=entry_bar.open_time,
        raw_entry_price=raw,
        effective_entry_price=effective,
        fee_bps=policy.fee_bps,
        slippage_bps=policy.slippage_bps,
    )
