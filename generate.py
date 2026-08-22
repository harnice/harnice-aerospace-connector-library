"""Run every family generator. One call writes the entire library."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(directory, module_name):
    sys.path.insert(0, str(ROOT / directory))
    __import__(module_name).main()


if __name__ == "__main__":
    run("D38999", "d38999_generator")
    run("M85049", "m85049_generator")
    run("mighty_mouse", "mighty_mouse_generator")
    run("dsub", "dsub_generator")
    run("dsub", "microd_generator")
    run("thermocouple", "thermocouple_generator")
    run("M22759", "m22759_generator")
    run("M27500", "m27500_generator")
