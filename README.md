# ERG Transactions Exporter

Free yourself from the tyranny and limitations of ERG wallets!
This little tool will fetch your ERG address details from explorer API, and export them to Koinly CSV format.
Can be easily modified for any other format as well.

## Features

- ✅ Fetches transactions from Ergo Platform API
- ✅ Processes both regular ERG transactions and token transactions
- ✅ Handles wallet consolidation transactions
- ✅ Exports data to CSV files compatible with tax software (Koinly format)
- ✅ Robust error handling with automatic retries
- ✅ Progress tracking for large datasets
- ✅ Address validation
- ✅ Comprehensive test coverage

## Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)

## Installation

### Using Poetry (Recommended)

1. Install Poetry if you haven't already:
   ```bash
   pip install poetry
   ```

2. Install project dependencies:
   ```bash
   poetry install
   ```

### Using pip (Alternative)

If you prefer using pip, you can install dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```

## How to Use

1. **Configure your wallet addresses:**
   - Copy `sample_dotenv` to `.env`
   - Edit `.env` and set environment variable names with comma-separated wallet addresses
   - For best results, include all addresses your wallet uses (to track internal transfers correctly)

2. **Run the exporter:**
   ```bash
   # Using Poetry
   poetry run python export_all.py
   
   # Or without Poetry
   python3 export_all.py
   ```

3. **View the output:**
   - Transaction CSV files will be created in the current directory
   - Regular transactions: `{wallet_name}.csv`
   - Token transactions: `{wallet_name}_tokens.csv`

## Running Tests

The project includes comprehensive test coverage for validation, formatting, and transaction processing.

### Run all tests:
```bash
poetry run pytest
```

### Run tests with verbose output:
```bash
poetry run pytest -v
```

### Run tests with coverage report:
```bash
poetry run pytest --cov=. --cov-report=term-missing
```

### View HTML coverage report:
```bash
poetry run pytest --cov=. --cov-report=html
# Open htmlcov/index.html in your browser
```

## Project Structure

```
export-erg-transactions/
├── export_all.py          # Main script
├── pyproject.toml         # Poetry configuration and dependencies
├── requirements.txt       # Pip dependencies (legacy)
├── .env                   # Your wallet configuration (create from sample_dotenv)
├── sample_dotenv          # Example configuration file
├── tests/                 # Test suite
│   ├── test_validation.py           # Address validation tests
│   ├── test_formatting.py           # Formatting and CSV tests
│   ├── test_transaction_processing.py  # Transaction processing tests
│   └── test_token_processing.py     # Token processing tests
└── README.md              # This file
```

## Development

### Adding Dependencies

```bash
# Add a runtime dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name
```

### Code Quality

The codebase follows best practices:
- Type hints for all functions
- Comprehensive docstrings
- Modular design with helper functions
- Constants for magic numbers
- Robust error handling
- Input validation

## Changelog

**15.10.2025:** Major refactoring and improvements
- Converted to Poetry for dependency management
- Added comprehensive test suite (44 tests, 100% pass rate)
- Refactored token processing with helper functions
- Added type hints throughout
- Improved code organization and maintainability
- Added validation for asset decimals
- Centralized CSV schema management

**13.10.2025:** Refactor and cleanup
- Updated libraries
- Added progress meter for larger amounts of transactions

**Initial Release:** Basic functionality
- Transaction fetching from Ergo Platform API
- CSV export in Koinly format

## License

MIT

## Contributing

Contributions are welcome! Please ensure:
1. All tests pass: `poetry run pytest`
2. Code follows existing style and conventions
3. New features include appropriate tests

