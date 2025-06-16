import logging
from dataclasses import asdict
from functools import singledispatch
from typing import Any

from omegaconf import DictConfig, OmegaConf


def get_dict_str_list(dt: dict[str, Any], indent: int = 2) -> list[str]:
    strings = []
    for k, v in dt.items():
        ind_str = " " * indent + "- "
        if isinstance(v, dict):
            strings.append(f"{ind_str}{k}:")
            strings.extend(get_dict_str_list(v, indent + 2))
        else:
            strings.append(f"{ind_str}{k}: {v}")
    return strings


def get_dict_str(dt: dict[str, Any], indent: int = 2) -> str:
    return "\n".join(["", *get_dict_str_list(dt, indent=indent), ""])


def print_dict(dt: dict[str, Any], indent: int = 2) -> None:
    print(get_dict_str(dt, indent=indent))


def print_dataclass(dc: Any) -> None:  # dataclass instance
    print("=========== Data Class ============")
    print_dict(asdict(dc))
    print("===================================")


# ---------------------------------------------------------
#                         Log Cfg
# ---------------------------------------------------------


@singledispatch
def cfg_to_loggable_lines(cfg: dict[str, Any] | DictConfig | Any) -> list[str]:
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


def get_cfg_str(cfg: dict[str, Any] | DictConfig | Any) -> str:
    return "\n".join(
        [
            "\n",
            "=" * 19 + "   Config   " + "=" * 19,
            *cfg_to_loggable_lines(cfg),
            "=" * 50,
            "",
        ]
    )


def log_cfg_str(cfg: dict[str, Any] | DictConfig | Any) -> None:
    logging.info(get_cfg_str(cfg))
