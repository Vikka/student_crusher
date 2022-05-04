import argparse
import csv
import importlib.util
from functools import cache
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Sequence, IO

from helper.clean_code import ast_clean
from helper.report import Report


def dir_validator(folder: str) -> Path:
    path = Path(folder).resolve()
    if not path.is_dir():
        raise ValueError(f"{folder} is not a valid folder")
    return path


def parse_args(args: Sequence[str] | None = None) -> tuple[Path, Path | None]:
    parser = argparse.ArgumentParser(description='Run a moulinette to onto a folder')
    parser.add_argument('target_folder', help='A folder with a moulinette.py inside',
                        type=dir_validator)
    parser.add_argument('-o', '--output', help='The output file', type=Path)

    namespace = parser.parse_args(args)
    return namespace.target_folder, namespace.output


@cache
def extract_module_from_path(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(moulinette: ModuleType, file: Path) -> Report:
    """
    Function that runs the moulinette
    """
    report = Report(file.stem)

    new_code, report = ast_clean(file.read_text(), report)
    spec = importlib.util.spec_from_loader(file.stem, loader=None)
    module = importlib.util.module_from_spec(spec)

    try:
        exec(new_code, module.__dict__)
    except Exception as e:
        report.add_malus_note(f"Error: {e}", 1)
        return report

    moulinette.run(module, report)
    return report


def run_moulinette_on_folder(target: Path) -> list[Report]:
    moulinette = extract_module_from_path('moulinette', target / 'moulinette.py')

    reports: list[Report] = list()
    for file in target.iterdir():
        if not file.is_file() or file.suffix != '.py' or file.name == 'moulinette.py':
            continue

        reports.append(run(moulinette, file))

    return reports


def to_csv(reports: list[Report], output: IO | None = None):
    """
    Function that prints the reports in a csv format
    """
    if output is None:
        output = StringIO()
    writer = csv.writer(output, delimiter=';')
    headers = ['Student', 'Grade', 'Comment']

    writer.writerow(headers)
    for report in reports:
        writer.writerow([report.student_name, report.score, ', '.join(report.notes)])

    if isinstance(output, StringIO):
        print(output.getvalue())


def mouli_runner(args: Sequence[str] | None = None):
    target, output = parse_args(args)
    reports = run_moulinette_on_folder(target)

    if output is not None:
        with output.open('w', newline='') as f:
            to_csv(reports, f)
    else:
        to_csv(reports)

    return True


if __name__ == '__main__':
    mouli_runner()
