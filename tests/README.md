# DexKeeper Bot Testing

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_helpers.py -v
```

## Test Coverage

- `test_helpers.py`: Unit tests for pure utility functions
- Additional integration tests can be added as needed

## Notes

These tests validate the bug fixes from the comprehensive bug sweep conducted in February 2026.
