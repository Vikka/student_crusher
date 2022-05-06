# Student Crusher

This project is a tool the run a "moulinette" on a folder of python file.

## Usage

The usage is simple:

```shell
$ python .\mouli_runner.py -h
usage: mouli_runner.py [-h] [-o OUTPUT] target_folder       

Run a moulinette to onto a folder

positional arguments:
  target_folder         A folder with a moulinette.py inside

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        The output file
```

You need to create a folder with a moulinette.py inside, and every other .py files inside will be
parsed, cleaned and send as a module to the moulinette.run function.

Here is an example of a moulinette.py:

```python
from types import ModuleType

from helper.report import Report


def exercice_1(module: ModuleType, report: Report) -> None:
    try:
        if not isinstance(module.my_list(1), list):
            report.add_note("my_list() should return a list")
        else:
            report.add_bonus_note('exercice_1 OK')
    except Exception as e:
        report.add_malus_note(f"Crash in test_exercice_1: {e}")


def run(module: ModuleType, report: Report) -> None:
    exercice_1(module, report)
```

## Example of use
```
> python .\mouli_runner.py .\exercice_1
student_1 started
student_2 started
student_3 started
student_4 started
Waiting for results...
student_1 done
student_2 done
student_3 done
student_4 done
Results received
Student;Grade;Comment
student_1;4;exercice_1 OK, exercice_2 OK, exercice_3 OK, exercice_4 OK
student_2;2;exercice_1 OK, exercice_2 OK, exercice_3 OK, Crash in test_exercice_4: Forbidden use of '+' on a list
student_3;4;exercice_1 OK, exercice_2 OK, exercice_3 OK, exercice_4 OK
student_4;-3;Forbidden names: sum, Forbidden attributes: insert, Error: expected an indented block after function definition on line 47 (<string>, line 49)
```