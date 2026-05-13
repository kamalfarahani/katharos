# Katharos Documentation

This directory contains the Sphinx documentation for Katharos, organized using the [Diátaxis framework](https://diataxis.fr/).

## Building the Documentation

### Prerequisites

Install documentation dependencies:

```bash
uv sync --group docs
```

### Build HTML Documentation

```bash
cd docs
uv run --group docs sphinx-build -b html . _build/html
```

Or use the Makefile:

```bash
cd docs
make html
```

The built documentation will be in `_build/html/`. Open `_build/html/index.html` in your browser.

### Build Other Formats

```bash
# PDF (requires LaTeX)
make latexpdf

# EPUB
make epub

# Plain text
make text
```

## Documentation Structure

Following the Diátaxis philosophy, documentation is organized into four categories:

- **tutorials/** - Learning-oriented lessons for beginners
- **how-to/** - Problem-oriented guides for specific tasks
- **reference/** - Information-oriented API documentation
- **explanation/** - Understanding-oriented conceptual discussions

## Writing Documentation

### Adding a New Tutorial

1. Create a new `.rst` file in `tutorials/`
2. Add it to `tutorials/index.rst`
3. Add it to the main `index.rst` toctree

### Adding API Documentation

API documentation is auto-generated from docstrings using Sphinx autodoc. To document a new module:

1. Ensure all docstrings follow Google-style format
2. Add the module to the appropriate file in `reference/api/`

### Docstring Format

Use Google-style docstrings:

```python
def example_function(arg1: int, arg2: str) -> bool:
    """Short description.
    
    Longer description with more details.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When something goes wrong
    
    Example:
        >>> example_function(42, "hello")
        True
    """
    pass
```

## Configuration

- `conf.py` - Sphinx configuration
- `_static/` - Static files (CSS, images)
- `_templates/` - Custom templates

## Theme

Documentation uses the [Furo](https://pradyunsg.me/furo/) theme with custom colors defined in `conf.py`.

## Continuous Integration

To integrate with CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Build documentation
  run: |
    uv sync --group docs
    cd docs
    uv run --group docs sphinx-build -b html . _build/html
```

## Troubleshooting

### Import Errors

If Sphinx can't import the package, check that `sys.path` is set correctly in `conf.py`.

### Missing Dependencies

Make sure all documentation dependencies are installed:

```bash
uv sync --group docs
```

### Build Warnings

Run with `-W` to treat warnings as errors:

```bash
uv run --group docs sphinx-build -W -b html . _build/html
```
