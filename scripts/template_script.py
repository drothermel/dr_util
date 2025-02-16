import logging

import hydra
from omegaconf import DictConfig

from dr_util.metrics import log_cfg


@hydra.main(version_base=None, config_path="../configs", config_name="base_config")
def run(cfg: DictConfig):
    log_cfg(cfg)
    logging.info(">> Welcome to your new script")
    logging.info(":: Goodbye ::")


if __name__ == "__main__":
    run()
