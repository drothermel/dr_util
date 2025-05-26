# dr_util
Core python utils for ML research

## Basic uv Functionality

Use uv to create the virtual environment:
```shell
# Currently 3.12.2
uv venv 3.12
```

Run tests with uv:
```shell
# Ensure pytest is installed first
uv run pytest
# -s will disable stdout capture so you can see what's printed
# -v for verbose
```

Format files:
```shell
uv run ruff format <optional:file>
```

Run ruff linter:
```shell
uv run ruff check

# or have it fix small errors
uv run ruff --fix
```

## Useful Features

- Roam API SDK + Example Notebook (`notebooks/roam_api.ipynb')

## Scripts

### S3Manager

Download files from s3: `uv run s3man`

Config setup:
```shell
# conf/s3man_config.yaml
defaults:
  source: refined

output:
  path_base: <my_coding_home>/data/
  file: refined/wiki_conf.json

# conf/s3man_source/refined.yaml
bucket: refined.public
key_path_base: 2022_oct/
key_name: wikipedia_model/config.json
```

**Design:** Any new source should setup the `bucket` and `key_path_base` so only `source.key_name` and `ouptut.file` are set via command line.

