import logging

import hydra
from dr_util.api_wrappers.aws_utils import S3Manager
from omegaconf import DictConfig

# To test downloading from s3:
#  uv run s3man 
#      source.key=wikipedia_model/config.json
#      output.file=refined/wikipedia_model_config.json

@hydra.main(version_base=None, config_path="../configs", config_name="s3man_config")
def main(cfg: DictConfig) -> None:
    logging.basicConfig(level="DEBUG")

    logging.info(">> Creating S3Manager and requesting file")
    s3m = S3Manager()
    s3m.download_file_if_needed(
        s3_bucket=cfg.s3man_source.bucket,
        s3_key=cfg.s3man_source.key,
        output_file_path_str=cfg.output.file,
    )


if __name__ == "__main__":
    main()
