import io
import json
import logging
import pickle
import sys
from pathlib import Path

import jsonlines
import numpy as np
from omegaconf import OmegaConf


def help_str():
    import_str = "import pathlib"
    path_props = [
        'p = pathlib.Path("/etc/a/b/d.json")' "p.name = d.json",
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
    ss = io.StringIO()
    ss.write("\n\n:: Useful Standard Lib Methods ::\n")
    ss.write(f'{"-" * 50}\n')
    ss.write(f"{import_str}\n")
    for st in [f" - {p}\n" for p in (*path_props, *construct_paths, *nav_dirs)]:
        ss.write(st)
    ss.write("Methods:\n")
    for mg in path_mthds:
        mm = ", ".join(mg)
        ss.write(f"  {mm}\n")
    return ss.getvalue()


def load_files(path_list):
    all_file_data = []
    for path in path_list:
        file_data = load_file(path)
        all_file_data.append(file_data)
    return all_file_data


def dump_file(data, path, force_suffix=None, *, verbose=True):
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
    dump_fxn = dump_lambdas.get(suffix)
    if dump_fxn is not None:
        dump_fxn(data, pl_path)
        if verbose:
            logging.info(f">> Dumped file: {path}")
        return True
    return False


def load_file(path, force_suffix=None, mmm=None, *, verbose=True):
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
    load_fxn = load_lambdas.get(suffix)
    if load_fxn is not None:
        data = load_fxn(pl_path)
        if verbose:
            logging.info(f">> Loaded file: {path}")
        return data

    logging.warning(f">> Path exists but can't load ending: {path}")
    return None


def loadjsonl(pl_path):
    return list(jsonlines.open(pl_path).iter(skip_empty=True))


def loadpkl(pl_path):
    return pickle.load(pl_path.open(mode="rb"))


def loadomega(pl_path):
    return OmegaConf.load(pl_path)


def dumptxt(data, pl_path, *, verbose=True):
    with pl_path.open(mode="w+") as f:
        f.write(data)
    if verbose:
        logging.info(f">> Dumped txt: {pl_path}")


def dumpjsonl(data, pl_path, *, verbose=True):
    with jsonlines.open(pl_path, mode="w") as writer:
        for line in data:
            writer.write(line)
    if verbose:
        logging.info(f">> Dumped jsonl: {pl_path}")


def dumpjson(data, pl_path, *, verbose=True):
    json.dump(data, pl_path.open(mode="w+"))
    if verbose:
        logging.info(f">> Dumped json: {pl_path}")


def dumppkl(data, pl_path, *, verbose=True):
    with pl_path.open(mode="wb") as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    if verbose:
        logging.info(f">> Dumped pkl: {pl_path}")


def dumpnpy(data, pl_path, *, verbose=True):
    np.save(pl_path, data)
    if verbose:
        logging.info(f">> Dumped npy: {pl_path}")


def dumpomega(data, pl_path, *, verbose=True):
    OmegaConf.save(data, f=pl_path)
    if verbose:
        logging.info(f">> Dumped OmegaConf: {pl_path}")


if __name__ == "__main__":
    from loguru import logger

    logger.remove()
    logger.add(sys.stdout, format="{time} | {message}", colorize=True)
    logger.info(help_str())
