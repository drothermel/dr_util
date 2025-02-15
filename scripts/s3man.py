import logging

import hydra
from omegaconf import DictConfig

import dr_util.log_utils as lu
from dr_util.api_wrappers.aws_utils import S3Manager

"""
This script downloads a file from s3 to a local destination.

To test downloading from s3:
    uv run s3man

Cfg fields you most likely want to modify
  s3man_source.bucket  = refined.public
  s3man_source.key     = 2022_oct/wikipedia_model/config.json
  s3man_source.out_dir_name = refined
  output.file_name     = wiki_conf.json
"""


@hydra.main(version_base=None, config_path="../configs", config_name="s3man")
def main(cfg: DictConfig) -> None:
    lu.log_cfg(cfg)

    logging.info(">> Creating S3Manager and requesting file")
    s3m = S3Manager()
    s3m.download_file_if_needed(
        s3_bucket=cfg.s3man_source.bucket,
        s3_key=cfg.s3man_source.key,
        output_file_path_str=cfg.output.file,
    )


if __name__ == "__main__":
    main()
