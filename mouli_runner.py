import argparse
import collections
import csv
import importlib.util
import multiprocessing
from functools import cache, partial
from io import StringIO
from multiprocessing import Pool, pool
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


def run_in_process(target, new_code, file, report) -> tuple[int, str]:
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
    return report


Results = collections.namedtuple('Results', ['report', 'async_res'])


def run(target: Path, file: Path, p: pool.Pool, reports: list[Report]) -> Results:
    """
    Function that runs the moulinette
    """
    report = Report(file.stem)
    try:
        cleaned_code, report = ast_clean(file.read_text(encoding='utf-8'), report)
    except UnicodeDecodeError as e:
        raise ValueError(f"{file.stem} is not a valid python file") from e
    final_code = ast_insert(cleaned_code) if cleaned_code else ''

    def callback(report_: Report):
        print(f"{file.stem} done")
        reports.append(report_)

    print(f"{file.stem} started")
    run_in_process_ = partial(run_in_process, target, final_code, file, report)
    async_res = p.apply_async(run_in_process_, callback=callback)
    return Results(report, async_res)


def run_moulinette_on_folder(target: Path) -> list[Report]:
    with Pool(50) as p:
        reports = []

        results = [
            (run(target, file, p, reports), file.stem)
            for file in target.iterdir()
            if file.is_file() and file.suffix == '.py' and file.name != 'moulinette.py'
        ]
    print("Waiting for results...")
    for r,  name in results:
        try:
            r.async_res.get(timeout=1)
        except multiprocessing.context.TimeoutError:
            report = r.report
            report.add_malus_note(f"Timeout")
            reports.append(report)

    return reports


def to_csv(reports: list[Report], output: IO | None = None):
    """
    Function that prints the reports in a csv format
    """
    if output is None:
        output = StringIO()
    writer = csv.writer(output, delimiter=';', escapechar='\\')
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

    for report in reports:
        if report.score == 20:
            report.add_note("Congratulations !")

    if output is not None:
        with output.open('w', newline='') as f:
            to_csv(reports, f)
    else:
        to_csv(reports)


if __name__ == '__main__':
    mouli_runner()
