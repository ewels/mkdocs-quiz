# MkDocs v2 compatibility

MkDocs v2.0 will remove the plugin system. It cannot run `mkdocs-quiz` or other MkDocs plugins. It also changes the theme system, so it is not a drop-in upgrade for an existing MkDocs 1.x site.

The `mkdocs-quiz` dependency is pinned to `mkdocs>=1.5,<2`. This prevents a routine dependency upgrade from silently installing MkDocs v2.0.

Additionally, Material for MkDocs is now in Maintainance Mode, with [end-of-life scheduled](https://github.com/squidfunk/mkdocs-material/issues/8523) for November 5, 2026.

Going forward, users of the `mkdocs-quiz` plugin have a few options:

## Stay on MkDocs 1.x

You can continue to use MkDocs 1.x with Material for MkDocs. The `mkdocs-quiz` version constraint keeps MkDocs below v2.0:

```bash
pip install mkdocs-quiz mkdocs-material
```

Build the site as usual:

```bash
mkdocs build
```

This is a completely fine strategy for now, though be aware that there is some risk
due to the upstream packages no longer getting security fixes.

## Use ProperDocs and MaterialX

[ProperDocs](https://properdocs.org/) is a compatible continuation of MkDocs 1.x. [MaterialX](https://jaywhj.github.io/mkdocs-materialx/differences.html) is a compatible fork of Material for MkDocs.

You can use either of them if you wish, in place of MkDocs or Material for MkDocs.

To install them both with mkdocs-quiz:

```bash
pip install mkdocs-quiz properdocs mkdocs-materialx
```

Set the theme name in `mkdocs.yml` or `properdocs.yml`:

```yaml
theme:
  name: materialx
```

Then use the ProperDocs command:

```bash
properdocs build
```

Material for MkDocs / MaterialX use the same `material` Python package. Install only one of these themes in each Python environment.

The mkdocs-quiz CI tests run on both stacks and I will do my best to keep the plugin working with both for as long as I can.

## Why mkdocs-quiz cannot depend on either package

Python package metadata cannot express a dependency for "`mkdocs` _or_ `properdocs`", it has to pick one. For now I'm keeping the dependency as `mkdocs>=1.5,<2`: ProperDocs users must install `properdocs` separately. This can leave the pinned MkDocs package installed but unused when you build with the `properdocs` command.

In the future we may remove the `mkdocs` dependency entirely and switch to `properdocs`.

## Further reading

- [What MkDocs 2.0 means for your documentation projects](https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/)
- [ProperDocs announcement](https://github.com/orgs/ProperDocs/discussions/33)
- [ProperDocs documentation](https://properdocs.org/)
- [MaterialX differences and migration notes](https://jaywhj.github.io/mkdocs-materialx/differences.html)
