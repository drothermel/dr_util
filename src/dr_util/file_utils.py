import io
import json
import logging
import pickle
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any

import jsonlines
import numpy as np
from omegaconf import OmegaConf


def fu_help() -> str:
    buff = io.StringIO()
    title_str = ":: Help for dr_util.file_utils ::"
    block_str = f" {'-' * len(title_str)} \n"

    buff.write(f"\n{title_str}\n")
    buff.write(f"{block_str}\n")
    buff.write(" For pathlib helpers: fu.pathlib_help()\n\n")
    buff.write(" Main Functions\n")
    buff.write("  - load_file(path, force_suffix=None, mmm=None, *, verbose=True)\n")
    buff.write("  - dump_file(data, path, force_suffix=None, verbose=Tue)\n")
    buff.write("  - load_files(path_list)\n")
    buff.write("  - jsonl_generator(path)\n\n")
    buff.write(" Supported Endings: json, jsonl, pkl, txt, npy, yaml\n")
    buff.write(f"\n{block_str}")

    buff_str = buff.getvalue()
    logging.info(buff_str)
    return buff_str


def pathlib_help() -> str:
    buff = io.StringIO()
    title_str = ":: Useful Standard Pathlib Methods ::"
    block_str = f" {'-' * len(title_str)} \n"
    buff.write(f"\n{title_str}\n")
    buff.write(f"{block_str}\n")

    import_str = "import pathlib"
    path_props = [
        'p = pathlib.Path("/etc/a/b/d.json")p.name = d.json',
        "p.suffix = .json",
        "p.parent = b",
        "p.parents = [/etc/a/b, /etc/a, /etc]",
        'p.stem = d, Path("a.tar.gz").stem = a.tar',
        "p.is_absolute() = True",
        'p.is_relative_to("/usr") = False',
        "p.exists() = True",
    ]
    construct_paths = [
        'p.with_name("df.zip") = /etc/a/df.zip',
        'p.with_stem("ab") = /etc/a/ab.zip',
        'p.with_suffix(".zip") = /etc/a/b.zip',
        'p / "init.d" = /etc/a/b.zip/init.d',
    ]
    nav_dirs = [
        "[x for x in p.iterdir() if p.is_dir()]",
        'list(p.glob("**/*.py")',
        "with p.open() as f: f.readline()",
    ]
    path_mthds = [
        [
            "cwd()",
            "home()",
            "exists(p)",
            "expanduser()",
            "is_file()",
            "is_dir()",
        ],
        [
            "is_symlink()",
            "mkdir(parents=False, exists_ok=False)",
            "rename(new_path_obj)",
        ],
        [
            "absolute()",
            "resolve()",
            "rglob()",
            "rmdir()",
            "touch()",
        ],
    ]

    buff.write(f" {import_str}\n")
    for st in [f"  - {p}\n" for p in (*path_props, *construct_paths, *nav_dirs)]:
        buff.write(st)
    buff.write("\n Methods:\n")
    for mg in path_mthds:
        mm = ", ".join(mg)
        buff.write(f"   {mm}\n")
    buff.write(f"\n{block_str}")

    buff_str = buff.getvalue()
    logging.info(buff_str)
    return buff_str


def jsonl_generator(path: str) -> Generator[Any, None, None]:
    with jsonlines.open(path) as reader:
        yield from reader


def load_files(path_list: list[str]) -> list[Any]:
    all_file_data = []
    for path in path_list:
        file_data = load_file(path)
        all_file_data.append(file_data)
    return all_file_data


def dump_file(
    data: Any,  # noqa: ANN401
    path: str,
    force_suffix: str | None = None,
    *,
    verbose: bool = True,
) -> bool:
    pl_path = Path(path)
    dump_lambdas = {
        "json": dumpjson,
        "jsonl": dumpjsonl,
        "pkl": dumppkl,
        "txt": dumptxt,
        "npy": dumpnpy,
        "yaml": dumpomega,
    }
    suffix = pl_path.suffix if force_suffix is None else force_suffix
    suffix = suffix.strip(".")
    dump_fxn = dump_lambdas.get(suffix)
    if dump_fxn is not None:
        dump_fxn(data, pl_path)
        if verbose:
            logging.info(f">> Dumped file: {path}")
        return True
    return False


def load_file(
    path: str,
    force_suffix: str | None = None,
    mmm: str | None = None,
    *,
    verbose: bool = True,
) -> Any:  # noqa: ANN401
    pl_path = Path(path)
    if not pl_path.exists():
        logging.warning(f">> Path missing: {path}")
    load_lambdas = {
        "json": lambda plp: json.load(plp.open()),
        "jsonl": loadjsonl,
        "pkl": loadpkl,
        "txt": lambda plp: plp.open().read(),
        "npy": lambda plp: np.load(plp) if mmm is None else np.load(plp, mmap_mode=mmm),
        "yaml": loadomega,
    }
    suffix = pl_path.suffix if force_suffix is None else force_suffix
    suffix = suffix.strip(".")
    load_fxn = load_lambdas.get(suffix)
    if load_fxn is not None:
        try:
            data = load_fxn(pl_path)
            if verbose:
                logging.info(f">> Loaded file: {path}")
        except (OSError, ValueError, KeyError, TypeError):
            data = None
        return data

    logging.warning(f">> Path exists but can't load ending: {path}")
    return None


def loadjsonl(pl_path: Path) -> list[Any]:
    return list(jsonlines.open(pl_path).iter(skip_empty=True))


def loadpkl(pl_path: Path) -> Any:  # noqa: ANN401
    return pickle.load(pl_path.open(mode="rb"))


def loadomega(pl_path: Path) -> Any:  # noqa: ANN401
    return OmegaConf.load(pl_path)


def dumptxt(data: str, pl_path: Path, *, verbose: bool = True) -> None:
    with pl_path.open(mode="w+") as f:
        f.write(data)
    if verbose:
        logging.info(f">> Dumped txt: {pl_path}")


def dumpjsonl(data: list[Any], pl_path: Path, *, verbose: bool = True) -> None:
    with jsonlines.open(pl_path, mode="w") as writer:
        for line in data:
            writer.write(line)
    if verbose:
        logging.info(f">> Dumped jsonl: {pl_path}")


def dumpjson(data: Any, pl_path: Path, *, verbose: bool = True) -> None:  # noqa: ANN401
    json.dump(data, pl_path.open(mode="w+"))
    if verbose:
        logging.info(f">> Dumped json: {pl_path}")


def dumppkl(data: Any, pl_path: Path, *, verbose: bool = True) -> None:  # noqa: ANN401
    with pl_path.open(mode="wb") as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    if verbose:
        logging.info(f">> Dumped pkl: {pl_path}")


def dumpnpy(data: Any, pl_path: Path, *, verbose: bool = True) -> None:  # noqa: ANN401
    np.save(pl_path, data)
    if verbose:
        logging.info(f">> Dumped npy: {pl_path}")


def dumpomega(data: Any, pl_path: Path, *, verbose: bool = True) -> None:  # noqa: ANN401
    OmegaConf.save(data, f=pl_path)
    if verbose:
        logging.info(f">> Dumped OmegaConf: {pl_path}")


if __name__ == "__main__":
    from loguru import logger

    logger.remove()
    logger.add(sys.stdout, format="{time} | {message}", colorize=True)
    fu_help()
    pathlib_help()
