# DexKeeper Bot Testing

## Running Tests

```bash
# Create a virtual environment from the repo root
python3 -m venv .venv
. .venv/bin/activate

# Install runtime + developer dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt -r requirements-dev.txt

# Run all tests
python3 -m pytest tests/ -v

# Run a specific test file
python3 -m pytest tests/test_helpers.py -v
```

## Test Coverage

- `test_helpers.py`: Utility helper coverage
- `test_bug_fixes.py`: Regression coverage for audited runtime bugs
- `test_conversation_flows.py`: Conversation state and input-flow coverage
- `test_telegram_simulation.py`: Telegram interaction simulation coverage

## Notes

These tests validate the current audited runtime behavior. They do not replace live Telegram validation for permissions, delivery, or forum configuration.
