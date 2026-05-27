"""Sphinx configuration for Katharos documentation."""

import sys
import tomllib
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

project = "Katharos"
copyright = f"{datetime.now().year}, Kamal Farahani"

# Read version and author from pyproject.toml
pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
with open(pyproject_path, "rb") as f:
    pyproject = tomllib.load(f)
    version = release = pyproject["project"]["version"]
    author = pyproject["project"]["authors"][0]["name"]

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "QUICK_START.md", "README.md"]

html_theme = "furo"
html_static_path = ["_static"]
html_logo = "../logo.png"
html_title = f"{project} {version}"

html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#7C3AED",
        "color-brand-content": "#7C3AED",
    },
    "dark_css_variables": {
        "color-brand-primary": "#A78BFA",
        "color-brand-content": "#A78BFA",
    },
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

todo_include_todos = True

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
