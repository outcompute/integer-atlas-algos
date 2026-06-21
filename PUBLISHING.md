# Releasing integer-atlas-algos to PyPI

Releases are driven from GitHub Actions using **PyPI Trusted Publishing** (OIDC — no
stored API tokens). The package is `integer-atlas-algos`; the command is `atlas-algos`.

## One-time setup

1. Add `authors` to `pyproject.toml` (the URLs and other metadata are already set).
2. Create GitHub Environments (Settings → Environments): `pypi`, and optionally
   `testpypi`. Add required reviewers on `pypi` for a manual approval gate if you want one.
3. Configure PyPI Trusted Publishing **before the first release** (a "pending publisher")
   at https://pypi.org → Account → Publishing → Add a pending publisher:
   - Project name: `integer-atlas-algos`
   - Owner: `outcompute`
   - Repository name: `integer-atlas-algos`
   - Workflow filename: `release.yml`
   - Environment name: `pypi`

   Repeat on https://test.pypi.org (environment `testpypi`, workflow `testpypi.yml`) to
   enable the dry-run upload.

## Workflows

- `ci.yml` — on push/PR: installs `.[parquet,hash,dev]` across Python 3.10–3.13 and runs
  the test suite (covers the Parquet and native-BLAKE3 paths).
- `release.yml` — on a `v*` tag: builds the wheel + sdist and publishes to PyPI via OIDC.
- `testpypi.yml` — manual (`workflow_dispatch`): same build, publishes to TestPyPI.

## Cutting a release

1. Bump `__version__` in `integer_atlas_algos/__init__.py` (PyPI rejects re-uploads of an
   existing version).
2. Merge to `main` once CI is green.
3. (Optional) Run the TestPyPI workflow, then verify
   `pip install -i https://test.pypi.org/simple/ integer-atlas-algos`.
4. Tag and push — `release.yml` publishes to PyPI:
   ```
   git tag v0.1.0 && git push origin v0.1.0
   ```

## Manual fallback

```
python3 -m pip install --upgrade build twine
rm -rf dist && python3 -m build
python3 -m twine check dist/*
python3 -m twine upload dist/*        # TWINE_USERNAME=__token__  TWINE_PASSWORD=<token>
```

## Notes

- Import name `integer_atlas_algos`; command `atlas-algos`.
- `dist/`, `build/`, `*.egg-info/` are git-ignored.
- `tools/` and `tests/` ship in the sdist but not the wheel.
