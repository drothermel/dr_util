import logging

import hydra
from dr_util.api_wrappers.aws_utils import S3Manager
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path="../configs", config_name="s3man_config")
def main(cfg: DictConfig) -> None:
    logging.basicConfig(level="DEBUG")

    # Recombine cfg into S3Manager inputs
    source = cfg.s3man_source
    bucket = source.bucket
    key = f"{source.key_path_base}{source.key_name}"
    outpath = f"{cfg.output.path_base}{cfg.output.file}"

    logging.info(">> Creating S3Manager and requesting file")
    s3m = S3Manager()
    s3m.download_file_if_needed(
        s3_bucket=bucket,
        s3_key=key,
        output_file_path_str=outpath,
    )


if __name__ == "__main__":
    main()
