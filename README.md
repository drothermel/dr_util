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

## Scripts

### S3Manager

Download files from s3: `rye run s3man`

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

