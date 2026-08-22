# Harnice Aerospace Connector Library

If you would like to add part families to this library, either submit a PR yourself, or create an issue with the details you'd like to see.

## Generating the library

Each family emitter writes its entire catalog. `generate.py` calls every emitter.

```bash
python generate.py                 # entire library
python D38999/d38999_generator.py  # one family
python check.py                    # CI merge gate
```

`check.py` recomputes every SKU from the family Python and fails if the committed files disagree. `main` requires the **check family catalogs** status check. CI installs [Harnice](https://github.com/harnice/Harnice) and runs `python check.py`.
