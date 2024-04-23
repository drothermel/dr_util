import sys
import io



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
    ss.write(f'{import_str}\n')
    for st in [f" - {p}\n" for p in (*path_props, *construct_paths, *nav_dirs)]:
        ss.write(st)
    ss.write("Methods:\n")
    for mg in path_mthds:
        mm = ", ".join(mg)
        ss.write(f"  {mm}\n")
    return ss.getvalue()

if __name__ == "__main__":
    from loguru import logger
    logger.remove()
    logger.add(sys.stdout, format="{time} | {message}", colorize=True)
    logger.info(help_str())
