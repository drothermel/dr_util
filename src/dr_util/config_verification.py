import logging
from functools import singledispatch

from omegaconf import DictConfig, OmegaConf

# ---------------------------------------------------------
#                         Log Cfg
# ---------------------------------------------------------


@singledispatch
def cfg_to_loggable_lines(cfg):
    logging.warning(f">> Unexpected cfg type: {type(cfg)}")
    return [str(cfg)]  # default, just stringify


@cfg_to_loggable_lines.register(dict)
def _(cfg):
    cfg_str = str(cfg)
    return cfg_str.strip("\n").split("\n")


@cfg_to_loggable_lines.register(DictConfig)
def _(cfg):
    resolved_cfg = OmegaConf.to_container(cfg, resolve=True)
    cfg_str = OmegaConf.to_yaml(resolved_cfg)
    return cfg_str.strip("\n").split("\n")


def get_cfg_str(cfg):
    return "\n".join(
        [
            "\n",
            "=" * 19 + "   Config   " + "=" * 19,
            *cfg_to_loggable_lines(cfg),
            "=" * 50,
            "",
        ]
    )


# ---------------------------------------------------------
#                         Validate Cfg
# ---------------------------------------------------------


def validate_cfg(cfg, config_type, schema_fxn):
    # Select the schema to validate with
    schema_cls = schema_fxn(config_type)
    if schema_cls is None:
        logging.error(f">> Invalid config schema type: {config_type}")
        return False

    # Get the missing keys
    bad_keys = get_bad_keys_by_schema(cfg, schema_cls)
    if len(bad_keys) > 0:
        logging.error(f">> Invalid config, missing or invalid keys: {bad_keys}")
        logging.error(get_cfg_str(cfg))
        return False
    return True


def get_bad_keys_by_schema(cfg, schema_cls):
    input_dict = OmegaConf.to_container(cfg, resolve=True)
    input_data_class = schema_cls(**input_dict, class_name="Top Level Config")
    return input_data_class.missing_or_invalid_keys
