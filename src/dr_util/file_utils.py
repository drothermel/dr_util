import sys
import io
import os
import jsonlines
import json
import pickle
import numpy as np
import glob
import logging
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


# ---------------- Untested or documented -------------------- #
# TODO: Update to use pathlib


def load_files(path_list, flatten=True):
    all_file_data = []
    for path in path_list:
        file_data = load_file(path)
        if flatten:
            all_file_data.extend(file_data)
        else:
            all_file_data.append(file_data)
    return all_file_data


def dump_file(data, path, ending=None, verbose=True):
    dump_lambdas = {
        "json": dumpjson,
        "jsonl": dumpjsonl,
        "pkl": dumppkl,
        "txt": dumptxt,
        "npy": dumpnpy,
        "yaml": dumpomega,
    }
    _, pe = get_name_ending_from_path(path)
    for e, dump_fxn in dump_lambdas.items():
        if ending == e or (ending is None and pe == e):
            dump_fxn(data, path)
            if verbose:
                logging.info(f">> Dumped file: {path}")
            return True
    assert False, f">> Can't dump ending: {path}"


def load_file(path, ending=None, mmm=None, verbose=True):
    assert os.path.exists(path), f">> Path doesn't exist: {path}"
    load_lambdas = {
        "json": lambda p: json.load(open(p)),
        "jsonl": loadjsonl,
        "pkl": loadpkl,
        "txt": lambda p: open(p).read(),
        "npy": lambda p: np.load(p) if mmm is None else np.load(p, mmap_mode=mmm),
        "yaml": loadomega,
    }
    data = None
    _, pe = get_name_ending_from_path(path)
    for e, load_fxn in load_lambdas.items():
        if ending == e or (ending is None and pe == e):
            data = load_fxn(path)
            if verbose:
                logging.info(f">> Loaded file: {path}")
            return data
    assert False, f">> Path exists but can't load ending: {path}"


def loadjsonl(filename):
    all_lines = []
    with jsonlines.open(filename) as reader:
        for obj in reader:
            all_lines.append(obj)
    return all_lines


def loadpkl(filename):
    return pickle.load(open(filename, "rb"))


def loadomega(filename):
    return OmegaConf.load(filename)


def dumptxt(data, path, verbose=True):
    with open(path, "w+") as f:
        f.write(data)
    if verbose:
        logging.info(f">> Dumped txt: {path}")


def dumpjsonl(data, path, verbose=True):
    with jsonlines.open(path, mode="w") as writer:
        for line in data:
            writer.write(line)
    if verbose:
        logging.info(f">> Dumped jsonl: {path}")


def dumpjson(data, path, verbose=True):
    json.dump(data, open(path, "w+"))
    if verbose:
        logging.info(f">> Dumped json: {path}")


def dumppkl(data, path, verbose=True):
    with open(path, "wb") as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    if verbose:
        logging.info(f">> Dumped pkl: {path}")


def dumpnpy(data, path, verbose=True):
    np.save(path, data)
    if verbose:
        logging.info(f">> Dumped npy: {path}")


def dumpomega(data, path, verbose=True):
    OmegaConf.save(data, f=path)
    if verbose:
        logging.info(f">> Dumped OmegaConf: {path}")


if __name__ == "__main__":
    from loguru import logger

    logger.remove()
    logger.add(sys.stdout, format="{time} | {message}", colorize=True)
    logger.info(help_str())
