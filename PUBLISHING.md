# Publishing Algos to PyPI — GitHub-managed

Goal: `pip install integer-atlas-algos`, releases driven entirely from GitHub via
Actions + **PyPI Trusted Publishing** (OIDC — no API tokens stored anywhere).

Assumes the **Algos repo is its own GitHub repository** (repo root = this `algos/`
directory). If you instead keep a monorepo with `algos/` as a subdirectory, add
`defaults.run.working-directory: algos` to the workflow jobs and a `paths:` filter
to `ci.yml`.

## Status: packaging is done

- Installable package `integer_atlas_algos/` (flat layout), all imports package-qualified.
- `pyproject.toml` configured: hatchling, dynamic version from
  `integer_atlas_algos/__init__.py`, `atlas-algos` console script, `parquet`/`hash`/`dev`
  extras, primes table shipped via `artifacts`.
- Build + clean-venv install verified locally (`atlas-algos` runs standalone, all three
  hashes populate, primes data ships).
- Workflows are committed under `.github/workflows/`: `ci.yml`, `release.yml`, `testpypi.yml`.

## One-time setup

1. **Create the GitHub repo** and push this directory to it (`main` branch).
2. **Fill metadata** in `pyproject.toml`: `authors`, and `[project.urls]`
   (Homepage/Source → the new repo). Confirm `license`.
3. **Create GitHub Environments** (repo → Settings → Environments): `pypi` and
   (optional) `testpypi`. Add required reviewers on `pypi` if you want a manual approval
   gate before each publish.
4. **Configure PyPI Trusted Publishing** (do this *before* the first release, as a
   "pending publisher"): on https://pypi.org → Account → Publishing → Add a pending
   publisher:
   - PyPI Project Name: `integer-atlas-algos`
   - Owner: your GitHub user/org
   - Repository name: the Algos repo
   - Workflow filename: `release.yml`
   - Environment name: `pypi`
5. (Optional) Repeat step 4 on https://test.pypi.org with Environment `testpypi` and
   workflow `testpypi.yml`.

No tokens are created or stored — OIDC handles auth at publish time.

## The workflows

- **`ci.yml`** — on every push to `main` and every PR: installs `.[parquet,hash,dev]`
  across Python 3.10–3.13 and runs the unittest suite (so parquet + native blake3 paths
  are covered in CI).
- **`release.yml`** — on a pushed tag `v*`: builds the wheel + sdist and publishes to
  PyPI via OIDC (environment `pypi`).
- **`testpypi.yml`** — manual (`workflow_dispatch`): same build, publishes to TestPyPI
  (environment `testpypi`) for a dry run.

## Cutting a release

1. Bump `__version__` in `integer_atlas_algos/__init__.py` (SemVer). PyPI rejects
   re-uploads of an existing version.
2. Open a PR; merge to `main` once CI is green.
3. (Optional) Run the **TestPyPI** workflow from the Actions tab and verify
   `pip install -i https://test.pypi.org/simple/ integer-atlas-algos`.
4. Tag and push:
   ```
   git tag v0.1.0
   git push origin v0.1.0
   ```
   `release.yml` builds and publishes to PyPI automatically.
5. (Optional) Create a GitHub Release from the tag for changelog/notes.

## Local manual fallback (if ever needed)

```
cd algos
python3 -m pip install --upgrade build twine
rm -rf dist && python3 -m build
python3 -m twine check dist/*
python3 -m twine upload dist/*        # needs TWINE_USERNAME=__token__ / TWINE_PASSWORD=<token>
```

## Notes

- PyPI **project name** `integer-atlas-algos` must be available; **import name** is
  `integer_atlas_algos`; **command** is `atlas-algos`.
- `dist/`, `build/`, `*.egg-info/` are git-ignored (see `.gitignore`).
- `tools/` and `tests/` ship in the sdist but not the wheel.
- This flow is for the **Python package only** (Algos). The CLI repo (Go) will use a
  different release path (e.g. GoReleaser → GitHub Releases); see the project-level
  integration TODO.
