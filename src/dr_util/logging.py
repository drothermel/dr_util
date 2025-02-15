from functools import singledispatch
from omegaconf import DictConfig, OmegaConf
import logging

@singledispatch
def cfg_to_loggable_lines(cfg):
    logging.warn(f">> Unexpected cfg type: {type(cfg)}")
    return [str(cfg)] # default, just stringify

@cfg_to_loggable_lines.register(dict)
def _(cfg):
    cfg_str = str(cfg)
    return cfg_str.strip("\n").split("\n")

@cfg_to_loggable_lines.register(DictConfig)
def _(cfg):
    resolved_cfg = OmegaConf.to_container(cfg, resolve=True)
    cfg_str = OmegaConf.to_yaml(resolved_cfg)
    return cfg_str.strip("\n").split("\n")
    
def log_cfg(cfg):
    cfg_log_str = '\n'.join([
        "\n",
        "=" * 19 + "   Config   " + "=" * 19,
        *cfg_to_loggable_lines(cfg),
        "=" * 50,
        "",
    ])
    logging.info(cfg_log_str)
