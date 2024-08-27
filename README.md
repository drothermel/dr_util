# dr_util
Core python utils for ML research

## Basic Rye Functionality

Use rye for choosing the python version:
```shell
# Currently 3.12.2
rye pin 3.12
```

Use rye to run tests:
```shell
# This works because we added pytest first as follows
rye add --dev pytest

# Then run the tests
rye test
# -s will disable stdout capture so you can see what's printed
# -v for verbose
```

Use rye to format files:
```shell
rye fmt <optional:file>
```

Use rye to run ruff linter:
```shell
rye lint

# or have it fix small errors
rye lint --fix
```




