import random

import hydra
from omegaconf import DictConfig

import dr_util.config_verification as cv
from dr_util.metrics import Metrics
from dr_util.schemas import get_schema


@hydra.main(version_base=None, config_path="../configs", config_name="base_config")
def run(cfg: DictConfig):
    if not cv.validate_cfg(cfg, "uses_metrics", get_schema):
        return

    # Make Metrics and Log Cfg
    md = Metrics(cfg)
    md.log(cfg)
    md.log(">> Welcome to your new script")

    # Use Metrics Class
    for ns in random.choices(range(1, 11), k=100):
        loss = random.random()
        md.train({"loss": loss, "num_samples": ns}, ns)
        md.val({"loss": loss - 0.5, "num_samples": ns}, ns)
    md.agg_log("train")
    md.agg_log("val")
    md.log(":: Goodbye ::")


if __name__ == "__main__":
    run()
