import logging
from functools import singledispatch
from typing import Any, cast

from omegaconf import DictConfig, OmegaConf

# ---------------------------------------------------------
#                         Log Cfg
# ---------------------------------------------------------


@singledispatch
def cfg_to_loggable_lines(cfg: Any) -> list[str]:
    logging.warning(f">> Unexpected cfg type: {type(cfg)}")
    return [str(cfg)]  # default, just stringify


@cfg_to_loggable_lines.register(dict)
def _(cfg: dict[str, Any]) -> list[str]:
    cfg_str = str(cfg)
    return cfg_str.strip("\n").split("\n")


@cfg_to_loggable_lines.register(DictConfig)
def _(cfg: DictConfig) -> list[str]:
    resolved_cfg = OmegaConf.to_container(cfg, resolve=True)
    cfg_str = OmegaConf.to_yaml(resolved_cfg)
    return cfg_str.strip("\n").split("\n")


def get_cfg_str(cfg: Any) -> str:
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


def validate_cfg(cfg: DictConfig, config_type: str, schema_fxn: Any) -> bool:
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


def get_bad_keys_by_schema(cfg: DictConfig, schema_cls: type) -> list[str]:
    input_dict = OmegaConf.to_container(cfg, resolve=True)
    assert isinstance(input_dict, dict), "Expected dict from OmegaConf.to_container"
    input_data_class = schema_cls(**cast(dict[str, Any], input_dict), class_name="Top Level Config")
    return list(input_data_class.missing_or_invalid_keys)
