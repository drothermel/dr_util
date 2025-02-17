import random

import hydra
from omegaconf import DictConfig

from dr_util.metrics import Metrics


@hydra.main(version_base=None, config_path="../configs", config_name="base_config")
def run(cfg: DictConfig):
    # Make Metrics and Log Cfg
    md = Metrics(cfg)
    md.log(">> Welcome to your new script")
    md.log(cfg)

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
