import logging
import hydra
from omegaconf import DictConfig, OmegaConf

@hydra.main(version_base=None, config_path="conf", config_name="s3man_config")
def main(cfg: DictConfig) -> None:
    logging.basicConfig(level="DEBUG")
    logging.info(f"Conf:\n {OmegaConf.to_yaml(cfg)}")

if __name__ == "__main__":
    main()

