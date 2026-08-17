# Installation

mkdocs-quiz requires Python 3.9 or later and [MkDocs](https://www.mkdocs.org/) 1.5 or later. It supports MkDocs 1.x, but not MkDocs 2.

The plugin supports both [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) and [MaterialX](https://jaywhj.github.io/mkdocs-materialx/). Do not install both themes in the same Python environment because they use the same `material` Python package.

See [MkDocs v2 compatibility](mkdocs-v2.md) for supported stacks and migration options.

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

## Choose a Material theme

=== "Material for MkDocs"

    Install Material for MkDocs:

    ```bash
    pip install mkdocs-material
    ```

    Set the theme name in `mkdocs.yml`:

    ```yaml
    theme:
      name: material
    ```

=== "MaterialX"

    Install MaterialX:

    ```bash
    pip install mkdocs-materialx
    ```

    Set the MaterialX theme name in `mkdocs.yml` or `properdocs.yml`:

    ```yaml
    theme:
      name: materialx
    ```

    MaterialX supports MkDocs 1.x and [ProperDocs](https://properdocs.org/). See the [MaterialX differences](https://jaywhj.github.io/mkdocs-materialx/differences.html) for migration details.

## Enabling the Plugin

Add the plugin to your `mkdocs.yml` configuration file:

```yaml
plugins:
  - mkdocs_quiz
```

That's it! The plugin is now active and will process all quiz blocks in your markdown files.

## Configuration

See the [Configuration](configuration.md) page for all available options.
