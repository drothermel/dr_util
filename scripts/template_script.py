import random

import hydra
from omegaconf import DictConfig

from dr_util.config_verification import validate_cfg
from dr_util.metrics import Metrics
from dr_util.schemas import get_schema
import dr_util.data_utils as du
import dr_util.determinism_utils as dtu


@hydra.main(version_base=None, config_path="../configs", config_name="base_config")
def run(cfg: DictConfig):
    if not validate_cfg(cfg, "uses_metrics", get_schema):
        return

    # Make Metrics and Log Cfg
    md = Metrics(cfg)
    md.log(cfg)
    md.log(">> Welcome to your new script! Loading CIFAR-10.")

    # Setup dataset (split_seed) and dataloader (seed)
    dataset = du.get_cifar_dataset(
        cfg.data.name,
        source_split=cfg.data.train.source_split,
        transform=None,
        root=cfg.paths.dataset_cache_root,
        download=cfg.data.download,
    )
    train_dataset, val_dataset = du.split_data(
        dataset, cfg.data.train.ratio, data_split_seed=cfg.data.split_seed,
    )
    generator = dtu.set_deterministic(cfg.seed)
    train_dl = du.get_dataloader(
        train_dataset,
        du.get_tensor_transform(),
        cfg.data.train.batch_size,
        cfg.data.train.shuffle,
        generator,
        cfg.data.num_workers,
    )

    for idx, (data, labels) in enumerate(train_dl):
        if idx > 2:
            break
        ns = len(data)
        loss = sum(labels).item()
        md.train({"loss": loss, "num_samples": ns}, ns)
        md.val({"loss": loss - 0.5, "num_samples": ns}, ns)
    md.agg_log("train")
    md.agg_log("val")
    md.log(":: Goodbye ::")


if __name__ == "__main__":
    run()
