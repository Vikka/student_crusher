import argparse
import importlib.util
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Sequence

from tabulate import tabulate


def file_validator(file: str) -> Path:
    path = Path(file).resolve()
    if not path.is_file():
        raise ValueError(f"{file} is not a valid file")
    return path


def dir_validator(folder: str) -> Path:
    path = Path(folder).resolve()
    if not path.is_dir():
        raise ValueError(f"{folder} is not a valid folder")
    return path


def parse_args(args: Sequence[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description='Run a moulinette to onto a folder')
    parser.add_argument('target_folder', help='A folder with a moulinette.py inside',
                        type=dir_validator)

    namespace = parser.parse_args(args)
    return namespace.target_folder


@cache
def extract_module_from_path(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_moulinette_on_folder(target: Path):
    moulinette = extract_module_from_path('moulinette', target / 'moulinette.py')

    results = list()

    for file in target.iterdir():
        if not file.is_file() or file.suffix != '.py' or file.name == 'moulinette.py':
            continue

        results.extend(moulinette.run(file))

    print(tabulate(results, headers=['Name', "Score", 'Result']))


def mouli_runner(args: Sequence[str] | None = None):
    target = parse_args(args)
    run_moulinette_on_folder(target)

    return True


if __name__ == '__main__':
    mouli_runner()
