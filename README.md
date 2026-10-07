# Causal Backtest Harness

Dependency-free Python primitives for explicit, machine-checkable signal-to-execution causality in quantitative backtests.

This project enforces execution semantics; it does not generate alpha.

## Causal contract

- signal becomes observable only after its signal bar closes;
- same-bar execution is forbidden;
- entry occurs at a strictly future bar open;
- default policy requires explicit completed-bar evidence;
- entry selection does not inspect future high/low/close values;
- malformed timing or candle geometry fails closed;
- entry slippage is adverse by side.

## Quick start

~~~python
from causal_backtest_harness import Bar, Side, execute_next_bar

result = execute_next_bar(
    bars,
    signal_index=0,
    side=Side.LONG,
)
~~~

## Relationship to Backtest Integrity Guard

`causal-backtest-harness` enforces causal mechanics while trades are generated.

`backtest-integrity-guard` independently audits exported OHLCV and ledger artifacts.

Together they provide defense in depth.

## Scope

No trading signals, strategy parameters, proprietary datasets, optimization logic, or private research rules are included.

## Development

~~~bash
python -m pip install .
python -m unittest discover -s tests -v
~~~
