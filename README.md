# Price Alert Tool — Wissen Technology

A modular, production-grade Python command-line application that ingests historical daily instrument prices from CSV files, evaluates configurable threshold and technical indicator rules from JSON specifications, detects state-transition crossings, and prints deterministic, formatted alerts.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Architecture & Directory Structure](#project-architecture--directory-structure)
- [Core Concepts & Rule Semantics](#core-concepts--rule-semantics)
  - [Price-Level Crossing (`level`)](#price-level-crossing-level)
  - [Moving-Average Crossover (`ma_cross`)](#moving-average-crossover-ma_cross)
  - [Deterministic Alert Ordering](#deterministic-alert-ordering)
- [Data Formats & Specifications](#data-formats--specifications)
  - [Prices CSV Specification](#prices-csv-specification)
  - [Rules JSON Specification](#rules-json-specification)
- [Installation & Setup](#installation--setup)
- [Usage Guide](#usage-guide)
  - [Command-Line Interface](#command-line-interface)
  - [Sample Execution & Output](#sample-execution--output)
  - [Error Handling & Exit Codes](#error-handling--exit-codes)
- [Testing & Quality Assurance](#testing--quality-assurance)
  - [Running the Test Suite](#running-the-test-suite)
  - [Test Fixture Matrix](#test-fixture-matrix)
  - [Verification Results](#verification-results)
- [AI Usage & Engineering Reflection](#ai-usage--engineering-reflection)

---

## Overview

In quantitative trading and portfolio monitoring, market participants must track real-time and historical price dynamics against fixed support/resistance thresholds and technical momentum indicators. The **Price Alert Tool** provides an automated engine for back-evaluating price datasets against customizable rule sets.

The tool processes daily closing prices across multiple equity or derivative instruments, validates all data integrity constraints, chronologically simulates price action, and surfaces crossing events without false duplicates or spurious repetitions.

---

## Key Features

- **Exact Decimal Arithmetic:** Utilizes Python's standard `decimal.Decimal` throughout indicator calculation and threshold comparisons to eliminate floating-point inaccuracies typical of binary representation.
- **Strict Data Validation:**
  - Enforces mandatory CSV header schema (`date,instrument,close`).
  - Validates ISO-8601 calendar dates (`YYYY-MM-DD`) and rejects non-existent dates (e.g., leap year anomalies).
  - Normalizes instrument tickers (case-insensitive ingestion).
  - Validates positive, finite numeric closing prices, rejecting negative, zero, NaN, or Infinite values.
  - Detects duplicate records (same date and instrument) and malformed row structures.
- **Crossing State Semantics:** Alerts trigger strictly on transition crossings (e.g., price crossing from `<= level` to `> level`), preventing persistent alerts when a price merely continues to hover above/below a threshold.
- **Multi-Window Moving Averages:** Computes rolling Simple Moving Averages (SMA) for arbitrary lookback periods (`short_window < long_window`), alerting when the short-term trend crosses the long-term trend.
- **Deterministic Alert Ordering:** Guarantees repeatable output sorted primarily by date (`YYYY-MM-DD` ascending) and secondarily by rule identifier (`rule_id` ascending).
- **Clean CLI Architecture:** Built on standard library `argparse` with dedicated console entry points, standard error streams (`stderr`), and POSIX-compliant exit codes (`0` for success, `1` for validation/IO failure).

---

## Technology Stack

- **Language:** Python 3.10+
- **Standard Library Modules:** `csv`, `json`, `decimal`, `argparse`, `dataclasses`, `pathlib`, `typing`, `collections.abc`
- **Testing Framework:** `pytest` (>= 9.0)
- **Packaging & Build System:** `setuptools` (>= 68.0), `wheel`

---

## Project Architecture & Directory Structure

The project adheres to modern Python packaging standards with a dedicated `src/` layout to prevent unintentional import side effects during testing.

```text
price-alert-tool-wissen-technology/
├── src/
│   └── price_alert/
│       ├── __init__.py
│       ├── cli.py                     # CLI entry point, argument parsing, error handling
│       ├── config.py                  # Configuration constants and defaults
│       ├── models/
│       │   ├── __init__.py
│       │   ├── price.py               # Price domain model (date, instrument, close: Decimal)
│       │   ├── rule.py                # Rule configuration dataclass
│       │   └── alert.py               # Triggered alert dataclass
│       ├── data/
│       │   ├── __init__.py
│       │   ├── csv_loader.py          # CSV reader and row validation pipeline
│       │   ├── rules_loader.py        # JSON rule deserialization and schema validation
│       │   └── validators.py          # Ingestion validators for dates, decimals, tickers
│       ├── indicators/
│       │   ├── __init__.py
│       │   └── moving_average.py      # Rolling SMA calculation with Decimal precision
│       ├── rules/
│       │   ├── __init__.py
│       │   ├── base.py                # Abstract BaseRule interface
│       │   ├── registry.py            # Rule registry mapping rule types to evaluators
│       │   ├── level_rule.py          # Level crossing evaluator (above / below)
│       │   └── ma_cross_rule.py       # SMA crossover evaluator (above / below)
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── evaluator.py           # Dispatches rules against sorted price histories
│       │   └── alert_engine.py        # Orchestrates multi-rule execution and sorting
│       ├── output/
│       │   ├── __init__.py
│       │   └── console.py             # Formatted alert renderer for stdout
│       └── exceptions/
│           ├── __init__.py
│           └── errors.py              # Domain-specific exception definitions
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/                      # 28 CSV fixtures covering valid & invalid edge cases
│   ├── unit/                          # Unit tests for loaders, rules, indicators, CLI
│   │   ├── test_alert_workflow.py
│   │   ├── test_cli.py
│   │   ├── test_csv_loader.py
│   │   ├── test_level_rule.py
│   │   ├── test_ma_cross_rule.py
│   │   ├── test_models.py
│   │   ├── test_moving_average.py
│   │   ├── test_output.py
│   │   ├── test_registry.py
│   │   └── test_rules_loader.py
│   └── integration/
│       └── test_alert_workflow.py     # End-to-end integration workflow tests
├── config/
│   └── rules.example.json             # Example alert rules configuration
├── examples/
│   └── prices.example.csv             # Example historical prices CSV
├── pyproject.toml                     # Build definition and pytest configuration
└── README.md                          # Project documentation
```

---

## Core Concepts & Rule Semantics

### Price-Level Crossing (`level`)

The `level` rule tracks when an instrument's daily closing price crosses a static price threshold.

- **`above` Direction:** Triggered on day $t$ if and only if:
  $$\text{Price}_{t-1} \le \text{Threshold} \quad \text{and} \quad \text{Price}_t > \text{Threshold}$$
- **`below` Direction:** Triggered on day $t$ if and only if:
  $$\text{Price}_{t-1} \ge \text{Threshold} \quad \text{and} \quad \text{Price}_t < \text{Threshold}$$

> **Note on State Persistence:** If the price remains above a threshold for multiple consecutive days, only the initial crossing day generates an alert.

### Moving-Average Crossover (`ma_cross`)

The `ma_cross` rule computes two Simple Moving Averages over lookback windows $S$ (short) and $L$ (long), where $S < L$:

$$\text{SMA}_k(t) = \frac{1}{k} \sum_{i=0}^{k-1} \text{Price}_{t-i}$$

An evaluation requires at least $L$ observations. A crossover is detected between day $t-1$ and day $t$ when:
- **`above` Direction (Bullish Crossover):**
  $$\text{SMA}_S(t-1) \le \text{SMA}_L(t-1) \quad \text{and} \quad \text{SMA}_S(t) > \text{SMA}_L(t)$$
- **`below` Direction (Bearish Crossover):**
  $$\text{SMA}_S(t-1) \ge \text{SMA}_L(t-1) \quad \text{and} \quad \text{SMA}_S(t) < \text{SMA}_L(t)$$

### Deterministic Alert Ordering

When multiple alerts occur across different dates, instruments, or rules, the engine guarantees deterministic ordering by sorting all alerts with the composite key:

```python
key = lambda alert: (alert.date, alert.rule_id)
```

1. **Primary Sort:** Date in ascending chronological order (`YYYY-MM-DD`).
2. **Secondary Sort:** Rule ID in ascending lexicographical order.

---

## Data Formats & Specifications

### Prices CSV Specification

The CSV file must be UTF-8 encoded with comma delimiters.

- **Header Requirement:** Must begin with exactly `date,instrument,close`.
- **Column Constraints:**
  - `date`: Valid calendar date in `YYYY-MM-DD` format. Unsorted records are automatically sorted chronologically.
  - `instrument`: Non-empty alphanumeric string (e.g., `ABC`, `XYZ`). Ingestion standardizes tickers to uppercase.
  - `close`: Strictly positive, finite numeric value (e.g., `100`, `105.75`). Exponential notation, NaNs, and infinities are rejected.

**Sample `prices.example.csv`:**
```csv
date,instrument,close
2026-01-01,ABC,100
2026-01-02,ABC,105
2026-01-03,ABC,115
2026-01-04,ABC,95
2026-01-05,ABC,110
2026-01-06,ABC,120
2026-01-01,XYZ,200
2026-01-02,XYZ,215
2026-01-03,XYZ,205
```

### Rules JSON Specification

The rules configuration file must contain a JSON array of rule objects.

#### Common Fields (All Rules)
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Unique identifier for the rule (e.g., `"ABC_LEVEL_1"`). Duplicate IDs are rejected. |
| `instrument` | `string` | Target instrument symbol to monitor (e.g., `"ABC"`). |
| `type` | `string` | Rule algorithm type: `"level"` or `"ma_cross"`. |
| `direction` | `string` | Crossing direction: `"above"` or `"below"`. |

#### Rule-Specific Fields
- **For `type == "level"`:**
  - `level`: Number (integer or float). Must be positive and finite.
- **For `type == "ma_cross"`:**
  - `short`: Positive integer representing the short SMA window.
  - `long`: Positive integer representing the long SMA window. Constraint: `short < long`.

**Sample `rules.example.json`:**
```json
[
  {
    "id": "ABC_LEVEL_1",
    "instrument": "ABC",
    "type": "level",
    "direction": "above",
    "level": 110
  },
  {
    "id": "ABC_MA_1",
    "instrument": "ABC",
    "type": "ma_cross",
    "direction": "above",
    "short": 2,
    "long": 3
  },
  {
    "id": "XYZ_LEVEL_1",
    "instrument": "XYZ",
    "type": "level",
    "direction": "below",
    "level": 210
  }
]
```

---

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/keshav62/price-alert-tool-wissen-technology.git
   cd price-alert-tool-wissen-technology
   ```

2. **Create and activate a virtual environment:**
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install the package in editable mode:**
   ```bash
   pip install -e .
   ```
   This registers the `price-alert` console script entry point defined in `pyproject.toml`.

---

## Usage Guide

### Command-Line Interface

The tool accepts two required CLI arguments:
- `--prices <path>`: Path to the input historical prices CSV file.
- `--rules <path>`: Path to the alert rules JSON configuration file.

```bash
price-alert --prices <path/to/prices.csv> --rules <path/to/rules.json>
```

Alternatively, invoke via Python's module syntax:
```bash
python -m price_alert.cli --prices <path/to/prices.csv> --rules <path/to/rules.json>
```

### Sample Execution & Output

Running against the bundled example files:

```bash
price-alert --prices examples/prices.example.csv --rules config/rules.example.json
```

**Console Output:**
```text
2026-01-03 | ABC_LEVEL_1 | ABC | level above 110
2026-01-03 | XYZ_LEVEL_1 | XYZ | level below 210
2026-01-06 | ABC_LEVEL_1 | ABC | level above 110
2026-01-06 | ABC_MA_1 | ABC | MA crossover above (short=115, long=108.3333333333333333333333333)
```

Each triggered alert line follows the format:
```text
YYYY-MM-DD | <RULE_ID> | <INSTRUMENT> | <ALERT_MESSAGE>
```

When no alerts match the given historical prices:
```text
No alerts detected.
```

### Error Handling & Exit Codes

The tool handles file and validation errors cleanly without raw stack traces in production:
- **Success (`Exit Code 0`):** File successfully parsed and rules evaluated (alerts printed or "No alerts detected.").
- **Failure (`Exit Code 1`):** Printed to `stderr` with informative diagnostics:
  - Missing or inaccessible files (`Error: [Errno 2] No such file or directory: ...`)
  - Malformed CSV headers or fields (`Error: CSV header must begin with 'date,instrument,close'`)
  - Schema violations in rules JSON (`Error: Rule at index 0: duplicate rule ID 'ABC_LEVEL_1'`)
  - Invalid MA windows (`Error: Rule at index 1: 'short' must be smaller than 'long'`)

---

## Testing & Quality Assurance

The project includes an exhaustive automated test suite implemented with `pytest`, covering unit functionality, data validation, boundary cases, and end-to-end integration workflows.

### Running the Test Suite

Execute the entire test suite from the repository root:

```bash
pytest
```

For verbose test outputs:
```bash
pytest -v
```

### Test Fixture Matrix

The `tests/fixtures/` directory maintains 28 standalone CSV fixtures designed to stress-test data ingestion and boundary edge cases:

| Fixture Category | Fixture Filenames | Validated Behavior |
|---|---|---|
| **Valid Datasets** | `valid_basic.csv`<br>`valid_single_row.csv`<br>`valid_multiple_instruments.csv`<br>`valid_unsorted_dates.csv`<br>`valid_decimal_prices.csv`<br>`valid_instrument_case.csv`<br>`valid_level_crossings.csv`<br>`valid_ma_crossover.csv`<br>`valid_large_dataset.csv`<br>`valid_header_only.csv` | Chronological sorting, multi-instrument isolation, decimal accuracy, ticker normalization, empty data handling, large dataset scalability. |
| **Header Validation** | `invalid_missing_header.csv`<br>`invalid_missing_date_column.csv`<br>`invalid_missing_instrument_column.csv`<br>`invalid_missing_close_column.csv`<br>`invalid_duplicate_headers.csv` | Enforces exact required column presence and rejects ambiguous or malformed headers. |
| **Row Structure** | `invalid_empty.csv`<br>`invalid_missing_field.csv`<br>`invalid_extra_field.csv` | Detects truncated rows, extra delimiters, and blank files. |
| **Data Integrity** | `invalid_date_format.csv`<br>`invalid_impossible_date.csv`<br>`invalid_empty_instrument.csv`<br>`invalid_empty_close.csv`<br>`invalid_non_numeric_close.csv`<br>`invalid_zero_close.csv`<br>`invalid_negative_close.csv`<br>`invalid_nan_close.csv`<br>`invalid_infinite_close.csv`<br>`invalid_duplicate_record.csv` | Strict rejection of unparseable dates, non-positive or non-finite prices, and duplicate date/instrument observations. |

### Verification Results

The latest test run validated the complete suite:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: E:\price-alert-tool-wissen-technology
configfile: pyproject.toml
testpaths: tests
collected 106 items

tests\unit\test_alert_workflow.py ..                                     [  1%]
tests\unit\test_cli.py ....                                              [  5%]
tests\unit\test_csv_loader.py .......................................... [ 45%]
.....                                                                    [ 50%]
tests\unit\test_level_rule.py ............                               [ 61%]
tests\unit\test_ma_cross_rule.py .........                               [ 69%]
tests\unit\test_models.py ...                                            [ 72%]
tests\unit\test_moving_average.py ..........                             [ 82%]
tests\unit\test_registry.py ...                                          [ 84%]
tests\unit\test_rules_loader.py ................                         [100%]

============================= 106 passed in 0.68s =============================
```

---

## AI Usage & Engineering Reflection

In accordance with assessment guidelines, this section documents the utilization of Artificial Intelligence tools during the development of this project.

### AI Tools & Prompts Used

- **Tool:** Google Antigravity AI pair programming assistant / Large Language Models.
- **Assistance Areas:**
  - **Project Scaffolding:** Drafting boilerplate directory trees, dataclasses, and abstract interfaces (`BaseRule`).
  - **Fixture Generation:** Generating combinatorial CSV edge-case datasets (e.g., impossible dates, decimal precision, whitespace-padded tickers).
  - **Test Case Expansion:** Generating comprehensive unit tests for `csv_loader.py` and `rules_loader.py` parameter validation.
  - **Debugging & Syntax Troubleshooting:** Diagnosing configuration syntax mismatches and CLI import paths.
  - **Documentation Drafting:** Structuring comprehensive markdown documentation and technical specifications.

### Review & Verification Strategy

All AI-suggested code, fixtures, and configurations underwent rigorous human review and verification:
1. **Manual Inspection:** Every generated file was independently inspected for logic correctness, PEP 8 styling, type hint completeness, and compliance with the specification.
2. **Deterministic Execution:** Code suggestions were tested by executing the CLI against known numerical datasets and validating that floating-point inaccuracies did not creep into Decimal computations.
3. **Automated Test Validation:** Every change was gated by running the full 106-test `pytest` suite locally.

### Real Development Issues Encountered & Solutions

During active development, three tangible issues were identified and resolved:

1. **Empty / Blank First Line in Example CSV:**
   - *Problem:* `examples/prices.example.csv` was initially created with an extraneous blank leading line. When ingested, `csv_loader.py` threw a validation error because line 1 did not match `date,instrument,close`.
   - *Identification & Resolution:* Detected during early CLI testing. The file was corrected to ensure the header starts strictly on line 1, and unit tests were added to confirm that empty-line anomalies are caught cleanly.
2. **PowerShell Here-String Syntax in JSON Configuration:**
   - *Problem:* When creating `config/rules.example.json` via a PowerShell script, PowerShell here-string syntax (`@" ... "@`) was inadvertently written into the physical file, causing `json.JSONDecodeError` upon parsing.
   - *Identification & Resolution:* Identified immediately when the rules loader rejected the file. The file was rewritten with valid standard JSON array syntax, and automated tests were verified to catch syntax errors with descriptive error messages.
3. **CLI Import Mismatch for Output Formatting:**
   - *Problem:* `src/price_alert/cli.py` was authored to import `from price_alert.output.console import print_alerts`. However, the initial output module did not export `print_alerts`, leading to an `ImportError` when running the CLI.
   - *Identification & Resolution:* Discovered when invoking `price-alert --help` and running `test_cli.py`. The `print_alerts` and `format_alert` functions were implemented in `console.py`, and corresponding unit tests were added in `test_output.py` and `test_cli.py`.

### Engineering Reflection

The use of AI significantly accelerated the creation of repetitive fixture permutations and boilerplate typing structures. However, engineering oversight was essential in defining strict crossing state semantics (ensuring alerts do not fire consecutively while on the same side of a threshold), selecting `decimal.Decimal` over native `float` for financial safety, and resolving integration defects between the CLI and presentation layers.
