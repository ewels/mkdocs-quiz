# Installation

mkdocs-quiz requires Python 3.8 or higher and [MkDocs](https://www.mkdocs.org/) 1.0.0 or higher.
It's designed to work with [mkdocs-material](https://squidfunk.github.io/mkdocs-material/), and is not guaranteed to work with other mkdocs themes.

=== "pip"

    To install mkdocs-quiz from PyPI, you can use pip:

    ```bash
    pip install mkdocs-quiz
    ```

    If your project has a `requirements.txt` file, add `mkdocs-quiz` to it and run:

    ```bash
    pip install -r requirements.txt
    ```

=== "uv"

    If you're managing your project with [uv](https://docs.astral.sh/uv/), you can add it as follows:

    ```bash
    uv add mkdocs-quiz
    ```

    Or to install globally:

    ```bash
    uv tool install mkdocs-quiz
    ```

=== "GitHub"

    For development or to get the latest unreleased features:

    ```bash
    git clone https://github.com/ewels/mkdocs-quiz.git
    cd mkdocs-quiz
    pip install -e ".[dev]"
    ```

## Enabling the Plugin

Add the plugin to your `mkdocs.yml` configuration file:

```yaml
plugins:
  - mkdocs_quiz
```

That's it! The plugin is now active and will process all quiz blocks in your markdown files.

## Configuration

See the [Configuration](configuration.md) page for all available options.
