# Harnice Aerospace Connector Library

If you would like to add part families to this library, either submit a PR yourself, or create an issue with the details you'd like to see.

## Generating the library

Each family has its own emitter (`{family}_generator.py`). `generate.py` at the repo root is the one command that can run all of them, count their catalogs, or check that the committed SKU folders still match.

```bash
python generate.py --list
python generate.py --dry-run
python generate.py --check
python generate.py --family D38999 --step-only
python generate.py                         # full generate, every family
```

`--step-only` writes attributes, drawings, and STEP envelopes without a Harnice product build. Cable families treat that flag as `--no-build`.

`--check` is the merge gate. It recomputes every SKU from the family Python (attributes, drawing envelope, catalog CSV) and compares that to the committed files. It does not write anything, so a local `python generate.py --check` and the CI job are the same check. If they disagree with the generators, the job fails.

`main` requires the **check family catalogs** status check. CI on pull requests and on `main` installs [Harnice](https://github.com/harnice/Harnice) and runs `python generate.py --check`.
