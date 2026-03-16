# Tools

This directory contains Python scripts that handle execution: API calls, data transformations, file operations, database queries, etc.

Each tool is:
- **Deterministic**: Produces consistent results
- **Testable**: Can be run independently
- **Fast**: Optimized for performance
- **Documented**: Clear inputs, outputs, and error handling

## Creating a Tool

1. Create a new `.py` file (e.g., `scrape_single_site.py`, `export_to_sheets.py`)
2. Include:
   - Clear argument parsing (use `argparse` for CLI tools)
   - Error handling with meaningful messages
   - Docstring explaining purpose and usage
   - Exit codes (0 for success, non-zero for failure)
   - Comments for complex logic

## Credentials

API keys and environment variables are stored in `.env` (never check in secrets):
```
API_KEY=your_key_here
DATABASE_URL=connection_string
```

Access in Python:
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('API_KEY')
```
