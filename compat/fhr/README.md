# fhr (renamed to fair-bioheaders)

The `fhr` package on PyPI is now
[`fair-bioheaders`](https://pypi.org/project/fair-bioheaders/), developed at
[FAIR-bioHeaders-Tools](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools).

This `fhr` distribution contains no code. It only depends on the matching version
of `fair-bioheaders`, so `pip install fhr` keeps installing the tools. Please
install `fair-bioheaders` directly instead:

```bash
python -m pip install fair-bioheaders
```

Everything that worked with `fhr` 0.3 keeps working:

- The `fhr-convert`, `fhr-validate`, `fhr-fasta-*`, and `fhr-gfa-*` commands are
  unchanged. The new `bioheaders` command offers the same operations as
  subcommands (`bioheaders convert`, `validate`, `combine`, `strip`, `verify`).
- `import fhr` and `from fhr.cli import ...` still work but emit a
  `DeprecationWarning`; use `import bioheaders` and `bioheaders.cli` instead.

To switch an existing environment from `fhr` 0.3 to `fair-bioheaders`, uninstall
the old distribution first, because both 0.3 and 0.4 install the `fhr` package
and `fhr-*` commands:

```bash
python -m pip uninstall fhr
python -m pip install fair-bioheaders
```

See the [changelog](https://github.com/FAIR-bioHeaders/FAIR-bioHeaders-Tools/blob/main/CHANGELOG.md)
for details.
