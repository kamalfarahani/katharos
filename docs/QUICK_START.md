# Documentation Quick Start

## Build Documentation

```bash
# Install dependencies (first time only)
uv sync --group docs

# Build HTML
cd docs
uv run --group docs sphinx-build -b html . _build/html

# View in browser
open _build/html/index.html
```

## Common Commands

```bash
# Clean build
rm -rf _build/

# Build with warnings as errors
uv run --group docs sphinx-build -W -b html . _build/html

# Build PDF (requires LaTeX)
make latexpdf

# Watch for changes (requires sphinx-autobuild)
uv run --group docs sphinx-autobuild . _build/html
```

## File Structure

```
docs/
├── index.rst              # Main landing page
├── conf.py                # Sphinx configuration
├── tutorials/             # Learning-oriented
├── how-to/                # Problem-oriented
├── reference/             # Information-oriented
│   └── api/              # Auto-generated API docs
└── explanation/           # Understanding-oriented
```

## Adding Content

### New Tutorial

1. Create `tutorials/my-tutorial.rst`
2. Add to `tutorials/index.rst`
3. Add to main `index.rst` toctree

### New API Module

1. Ensure docstrings are complete
2. Add to `reference/api/module-name.rst`
3. Use `.. automodule::` directive

## Docstring Format

```python
def example(arg: int) -> str:
    """Short description.
    
    Longer description.
    
    Args:
        arg: Description
    
    Returns:
        Description
    
    Example:
        >>> example(42)
        'result'
    """
```

## Troubleshooting

**Import errors:** Check `sys.path` in `conf.py`

**Missing dependencies:** Run `uv sync --group docs`

**Build warnings:** Run with `-W` flag to see details

## Links

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Furo Theme](https://pradyunsg.me/furo/)
- [Diátaxis Framework](https://diataxis.fr/)
- [Google Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
