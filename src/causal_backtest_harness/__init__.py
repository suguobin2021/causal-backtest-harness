"""Causal backtest execution primitives."""

from .core import (
    Bar,
    BarCompletionPolicy,
    ExecutionPolicy,
    ExecutionResult,
    ExecutionViolation,
    Side,
    execute_next_bar,
)

__all__ = [
    "Bar",
    "BarCompletionPolicy",
    "ExecutionPolicy",
    "ExecutionResult",
    "ExecutionViolation",
    "Side",
    "execute_next_bar",
]

__version__ = "0.1.0"
