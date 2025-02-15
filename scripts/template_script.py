import logging

import hydra
from omegaconf import DictConfig

import dr_util.logging as lu


@hydra.main(version_base=None, config_path="../configs", config_name="base_config")
def run(cfg: DictConfig):
    lu.log_cfg(cfg)
    logging.info(">> Welcome to your new script")
    logging.info(":: Goodbye ::")


if __name__ == "__main__":
    run()
