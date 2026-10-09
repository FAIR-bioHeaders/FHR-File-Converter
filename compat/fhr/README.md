# fhr (renamed to fair-bioheaders)

The `fhr` package on PyPI is now
[`fair-bioheaders`](https://pypi.org/project/fair-bioheaders/), developed at
[FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools).

This `fhr` distribution contains no code. It requires the same version of
`fair-bioheaders`, so `pip install fhr` and `pip install -U fhr` keep installing
the tools. For new installs and requirements, use `fair-bioheaders` directly:

```bash
python -m pip install fair-bioheaders
```

Everything that worked with `fhr` 0.3 keeps working:

- The `fhr-convert`, `fhr-validate`, `fhr-fasta-*`, and `fhr-gfa-*` commands are
  unchanged. The new `bioheaders` command offers the same operations as
  subcommands (`bioheaders convert`, `validate`, `combine`, `strip`, `verify`).
- `import fhr` and `from fhr.cli import ...` still work but emit a
  `DeprecationWarning`; use `import bioheaders` and `bioheaders.cli` instead.

This distribution also declares the `fhr-*` commands, so that upgrading from
`fhr` 0.3 with pip keeps them. If you later uninstall `fhr`, restore them with:

```bash
python -m pip install --force-reinstall --no-deps fair-bioheaders
```

In an environment that still has `fhr` 0.3, uninstall it before installing
`fair-bioheaders` on its own, or upgrade with `python -m pip install -U fhr`.

See the [changelog](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/blob/main/CHANGELOG.md)
for details.
