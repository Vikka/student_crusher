import argparse
import csv
import importlib.util
import time
from functools import cache, partial
from io import StringIO
from multiprocessing import Pool, pool
from multiprocessing.pool import ApplyResult
from pathlib import Path
from types import ModuleType
from typing import Sequence, IO

from helper.clean_code import ast_clean
from helper.insert_code import ast_insert
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
    parser.add_argument('-o', '--output',
                        help="The output file as a csv file with ';' as separator", type=Path)

    namespace = parser.parse_args(args)
    return namespace.target_folder, namespace.output


@cache
def extract_module_from_path(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def p_run(target, new_code, file, report):
    moulinette = extract_module_from_path('moulinette', target / 'moulinette.py')
    spec = importlib.util.spec_from_loader(file.stem, loader=None)
    module = importlib.util.module_from_spec(spec)
    try:
        exec(new_code, module.__dict__)
    except Exception as e:
        report.add_malus_note(f"Error: {e}", 1)
        return report

    try:
        moulinette.run(module, report)
    except Exception as e:
        report.add_note(f"Error: {e}")
    return report


def run(target: Path, file: Path, p: pool.Pool, reports: list[Report]) -> tuple[Report, ApplyResult[Report]]:
    """
    Function that runs the moulinette
    """
    report = Report(file.stem)
    cleaned_code, report = ast_clean(file.read_text(), report)
    final_code = ast_insert(cleaned_code) if cleaned_code else None

    def callback(report: Report):
        print(f"{file.stem} done")
        reports.append(report)

    print(f"{file.stem} started")
    partial_run = partial(p_run, target, final_code, file, report)
    async_res = p.apply_async(partial_run, callback=callback)
    return report, async_res


def run_moulinette_on_folder(target: Path) -> list[Report]:
    with Pool(5) as p:
        reports = []

        results = [
            (run(target, file, p, reports), file.stem) for file in
            target.iterdir()
            if file.is_file() and file.suffix == '.py' and file.name != 'moulinette.py'
        ]
        print("Waiting for results...")
        time.sleep(1)
    print("Results received")
    for r, name in results:
        if not r[1].ready():
            report = r[0]
            report.add_malus_note(f"Timeout")
            reports.append(report)
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
    else:
        print(f"Report saved in {output.name}")


def mouli_runner(args: Sequence[str] | None = None):
    target, output = parse_args(args)
    reports = run_moulinette_on_folder(target)

    if output is not None:
        with output.open('w', newline='') as f:
            to_csv(reports, f)
    else:
        to_csv(reports)


if __name__ == '__main__':
    mouli_runner()
