"""Allow the CLI to be run as ``python -m mkdocs_quiz.cli``.

Used by the ``check-translations`` pre-commit hook and CI, which need to run the
CLI straight from a source checkout without installing the package.
"""

from __future__ import annotations

from .main import main

if __name__ == "__main__":
    main()
