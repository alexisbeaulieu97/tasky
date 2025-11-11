# tasky-logging

Pluggable logging infrastructure for Tasky.

## Overview

This package provides a logging abstraction layer that allows swappable logging backends while maintaining a consistent interface for consumer packages.

## Features

- **Logger Protocol**: Type-safe logging interface for dependency injection
- **Factory Function**: `get_logger(name)` returns configured logger instances
- **Configuration**: `configure_logging(verbosity, format_style)` for CLI integration
- **Swappable Backends**: Currently uses stdlib logging, designed to support loguru and others

## Usage

```python
from tasky_logging import get_logger, configure_logging

# Configure logging (typically in CLI entry point)
configure_logging(verbosity=1, format_style="standard")

# Get a logger in your module
logger = get_logger("my_module")

# Use the logger
logger.info("Operation completed")
logger.debug("Detailed debug info")
logger.warning("Something unexpected happened")
```

## Verbosity Levels

- `0`: WARNING and above (default)
- `1`: INFO and above
- `2+`: DEBUG and above (all messages)

## Architecture

This package is part of Tasky's clean architecture:
- **Domain layers** (tasky-tasks, tasky-projects) use logging for operations
- **Infrastructure layers** (tasky-storage) use logging for I/O operations
- **Presentation layers** (tasky-cli) configure logging based on user preferences

The logging implementation can be swapped without changing consumer code.
