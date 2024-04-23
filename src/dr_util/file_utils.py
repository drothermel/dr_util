
def help():
    import_str = 'import pathlib'
    path_props = [
        'p = pathlib.Path("/etc/a/b/d.json")'
        'p.name = d.json',
        'p.suffix = .json',
        'p.parent = b',
        'p.parents = [/etc/a/b, /etc/a, /etc]',
        'p.stem = d, Path("a.tar.gz").stem = a.tar',
        'p.is_absolute() = True',
        'p.is_relative_to("/usr") = False',
        'p.exists() = True',
    ]
    construct_paths = [
        'p.with_name("df.zip") = /etc/a/df.zip',
        'p.with_stem("ab") = /etc/a/ab.zip',
        'p.with_suffix(".zip") = /etc/a/b.zip',
        'p / "init.d" = /etc/a/b.zip/init.d',
    ]
    nav_dirs = [
        '[x for x in p.iterdir() if p.is_dir()]',
        'list(p.glob("**/*.py")',
    ]
    other = [
        'with p.open() as f: f.readline()',
    ]
    path_mthds = [
        'cwd()',
        'home()',
        'exists(p)',
        'expanduser()',
        'is_file()',
        'is_dir()',
        'is_symlink()',
        'mkdir(parents=False, exists_ok=False)',
        'rename(new_path_obj)',
        'absolute()',
        'resolve()',
        'rglob()',
        'rmdir()', 
        'touch()',
    ]
    all_lines = []
    all_lines.append(import_str)
    for p in *path_props, *construct_paths, *nav_dirs:
        all_lines.append(f' - {p}')
    all_methods = ', '.join(path_mthds)
    all_lines.append(f'\nMethods: {all_methods}\n')

    print('-'*50)
    print(":: Useful Standard Lib Methods ::\n")
    for l in all_lines:
        print(l)
    print('-'*50)

if __name__ == "__main__":
    help()
