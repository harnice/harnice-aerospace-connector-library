import os
import json
import math
import subprocess
import sys

from harnice.lists import rev_history
from harnice import fileio, state
import harnice.products.part as part


def _load_step_utils():
    try:
        from harnice.utils import step_utils as module
        return module
    except ImportError:
        pass
    import importlib.util

    sibling = os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "Harnice",
            "src",
            "harnice",
            "utils",
            "step_utils.py",
        )
    )
    spec = importlib.util.spec_from_file_location("harnice_step_utils", sibling)
    if spec is None or spec.loader is None:
        raise ImportError(
            "Generating STEP envelopes requires harnice.utils.step_utils "
            "(Harnice src/harnice/utils/step_utils.py)."
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


step_utils = _load_step_utils()

REVISION = "1"
DATE_STARTED = "2/3/26"
delete_pngs = True

CONTACT_SIZES = {
    "12": {
        "awg_min": 12,
        "awg_max": 16,
        "current_rating": 23.0,
        "crimp_tool": "M22520/2-01",
        "extraction_tool": "M81969/14-03",
    },
    "16": {
        "awg_min": 16,
        "awg_max": 20,
        "current_rating": 13.0,
        "crimp_tool": "M22520/2-01",
        "extraction_tool": "M81969/14-04",
    },
    "20": {
        "awg_min": 20,
        "awg_max": 24,
        "current_rating": 7.5,
        "crimp_tool": "M22520/2-01",
        "extraction_tool": "M81969/14-05",
    },
    "22D": {
        "awg_min": 22,
        "awg_max": 26,
        "current_rating": 5.0,
        "crimp_tool": "M22520/2-01",
        "extraction_tool": "M81969/14-06",
    },
}

INSERT_ARRANGEMENTS = { # FOR REFERENCE ONLY - AI READ THE PDF, NOT A HUMAN
    "9-35": [
        {"name": "1", "size": "22D"},
        {"name": "2", "size": "22D"},
        {"name": "3", "size": "22D"},
        {"name": "4", "size": "22D"},
        {"name": "5", "size": "22D"},
        {"name": "6", "size": "22D"},
    ],
    "9-94": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
    ],
    "9-98": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
    ],
    "11-2": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
    ],
    "11-4": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
    ],
    "11-5": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
    ],
    "11-35": [
        {"name": "1", "size": "22D"},
        {"name": "2", "size": "22D"},
        {"name": "3", "size": "22D"},
        {"name": "4", "size": "22D"},
        {"name": "5", "size": "22D"},
        {"name": "6", "size": "22D"},
        {"name": "7", "size": "22D"},
        {"name": "8", "size": "22D"},
        {"name": "9", "size": "22D"},
        {"name": "10", "size": "22D"},
        {"name": "11", "size": "22D"},
        {"name": "12", "size": "22D"},
        {"name": "13", "size": "22D"},
    ],
    "11-54": [
        {"name": "A", "size": "22D"},
        {"name": "B", "size": "22D"},
        {"name": "C", "size": "22D"},
        {"name": "D", "size": "22D"},
    ],
    "11-98": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
    ],
    "11-99": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
    ],
    "13-4": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
        {"name": "C", "size": "16"},
        {"name": "D", "size": "16"},
    ],
    "13-8": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
    ],
    "13-26": [
        {"name": "A", "size": "22D"},
        {"name": "B", "size": "22D"},
        {"name": "C", "size": "22D"},
        {"name": "D", "size": "22D"},
        {"name": "E", "size": "22D"},
        {"name": "F", "size": "22D"},
        {"name": "G", "size": "12"},
        {"name": "H", "size": "12"},
    ],
    "13-35": [
        {"name": "1", "size": "22D"},
        {"name": "2", "size": "22D"},
        {"name": "3", "size": "22D"},
        {"name": "4", "size": "22D"},
        {"name": "5", "size": "22D"},
        {"name": "6", "size": "22D"},
        {"name": "7", "size": "22D"},
        {"name": "8", "size": "22D"},
        {"name": "9", "size": "22D"},
        {"name": "10", "size": "22D"},
        {"name": "11", "size": "22D"},
        {"name": "12", "size": "22D"},
        {"name": "13", "size": "22D"},
        {"name": "14", "size": "22D"},
        {"name": "15", "size": "22D"},
        {"name": "16", "size": "22D"},
        {"name": "17", "size": "22D"},
        {"name": "18", "size": "22D"},
        {"name": "19", "size": "22D"},
        {"name": "20", "size": "22D"},
        {"name": "21", "size": "22D"},
        {"name": "22", "size": "22D"},
    ],
    "13-63": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
        {"name": "C", "size": "12"},
        {"name": "D", "size": "12"},
    ],
    "13-98": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
    ],
    "15-4": [
        {"name": "A", "size": "12"},
        {"name": "B", "size": "12"},
        {"name": "C", "size": "12"},
        {"name": "D", "size": "12"},
    ],
    "15-5": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
        {"name": "C", "size": "16"},
        {"name": "D", "size": "16"},
        {"name": "E", "size": "16"},
    ],
    "15-15": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "16"},
        {"name": "R", "size": "20"},
    ],
    "15-18": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "16"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
    ],
    "15-19": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "16"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
    ],
    "15-35": [
        {"name": "1", "size": "22D"},
        {"name": "2", "size": "22D"},
        {"name": "3", "size": "22D"},
        {"name": "4", "size": "22D"},
        {"name": "5", "size": "22D"},
        {"name": "6", "size": "22D"},
        {"name": "7", "size": "22D"},
        {"name": "8", "size": "22D"},
        {"name": "9", "size": "22D"},
        {"name": "10", "size": "22D"},
        {"name": "11", "size": "22D"},
        {"name": "12", "size": "22D"},
        {"name": "13", "size": "22D"},
        {"name": "14", "size": "22D"},
        {"name": "15", "size": "22D"},
        {"name": "16", "size": "22D"},
        {"name": "17", "size": "22D"},
        {"name": "18", "size": "22D"},
        {"name": "19", "size": "22D"},
        {"name": "20", "size": "22D"},
        {"name": "21", "size": "22D"},
        {"name": "22", "size": "22D"},
        {"name": "23", "size": "22D"},
        {"name": "24", "size": "22D"},
        {"name": "25", "size": "22D"},
        {"name": "26", "size": "22D"},
        {"name": "27", "size": "22D"},
        {"name": "28", "size": "22D"},
        {"name": "29", "size": "22D"},
        {"name": "30", "size": "22D"},
        {"name": "31", "size": "22D"},
    ],
    "15-97": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "16"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "16"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "16"},
        {"name": "M", "size": "16"},
    ],
    "17-6": [
        {"name": "A", "size": "12"},
        {"name": "B", "size": "12"},
        {"name": "C", "size": "12"},
        {"name": "D", "size": "12"},
        {"name": "E", "size": "12"},
        {"name": "F", "size": "12"},
    ],
    "17-8": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
        {"name": "C", "size": "16"},
        {"name": "D", "size": "16"},
        {"name": "E", "size": "16"},
        {"name": "F", "size": "16"},
        {"name": "G", "size": "16"},
        {"name": "H", "size": "16"},
    ],
    "17-26": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "16"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "20"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "20"},
        {"name": "a", "size": "20"},
        {"name": "b", "size": "20"},
        {"name": "c", "size": "20"},
    ],
    "17-35": [
        {"name": "1", "size": "22D"},
        {"name": "2", "size": "22D"},
        {"name": "3", "size": "22D"},
        {"name": "4", "size": "22D"},
        {"name": "5", "size": "22D"},
        {"name": "6", "size": "22D"},
        {"name": "7", "size": "22D"},
        {"name": "8", "size": "22D"},
        {"name": "9", "size": "22D"},
        {"name": "10", "size": "22D"},
        {"name": "11", "size": "22D"},
        {"name": "12", "size": "22D"},
        {"name": "13", "size": "22D"},
        {"name": "14", "size": "22D"},
        {"name": "15", "size": "22D"},
        {"name": "16", "size": "22D"},
        {"name": "17", "size": "22D"},
        {"name": "18", "size": "22D"},
        {"name": "19", "size": "22D"},
        {"name": "20", "size": "22D"},
        {"name": "21", "size": "22D"},
        {"name": "22", "size": "22D"},
        {"name": "23", "size": "22D"},
        {"name": "24", "size": "22D"},
        {"name": "25", "size": "22D"},
        {"name": "26", "size": "22D"},
        {"name": "27", "size": "22D"},
        {"name": "28", "size": "22D"},
        {"name": "29", "size": "22D"},
        {"name": "30", "size": "22D"},
        {"name": "31", "size": "22D"},
        {"name": "32", "size": "22D"},
        {"name": "33", "size": "22D"},
        {"name": "34", "size": "22D"},
        {"name": "35", "size": "22D"},
        {"name": "36", "size": "22D"},
        {"name": "37", "size": "22D"},
        {"name": "38", "size": "22D"},
        {"name": "39", "size": "22D"},
        {"name": "40", "size": "22D"},
        {"name": "41", "size": "22D"},
        {"name": "42", "size": "22D"},
        {"name": "43", "size": "22D"},
        {"name": "44", "size": "22D"},
        {"name": "45", "size": "22D"},
        {"name": "46", "size": "22D"},
        {"name": "47", "size": "22D"},
        {"name": "48", "size": "22D"},
        {"name": "49", "size": "22D"},
        {"name": "50", "size": "22D"},
        {"name": "51", "size": "22D"},
        {"name": "52", "size": "22D"},
        {"name": "53", "size": "22D"},
        {"name": "54", "size": "22D"},
        {"name": "55", "size": "22D"},
    ],
    "17-99": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "16"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "16"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "16"},
    ],
    "19-11": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
        {"name": "C", "size": "16"},
        {"name": "D", "size": "16"},
        {"name": "E", "size": "16"},
        {"name": "F", "size": "16"},
        {"name": "G", "size": "16"},
        {"name": "H", "size": "16"},
        {"name": "J", "size": "16"},
        {"name": "K", "size": "16"},
        {"name": "L", "size": "16"},
    ],
    "19-28": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "16"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "20"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "16"},
        {"name": "a", "size": "20"},
        {"name": "b", "size": "20"},
        {"name": "c", "size": "20"},
        {"name": "d", "size": "20"},
        {"name": "e", "size": "16"},
    ],
    "19-32": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "16"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "20"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "16"},
        {"name": "a", "size": "20"},
        {"name": "b", "size": "20"},
        {"name": "c", "size": "20"},
        {"name": "d", "size": "20"},
        {"name": "e", "size": "16"},
        {"name": "f", "size": "20"},
        {"name": "g", "size": "20"},
        {"name": "h", "size": "20"},
        {"name": "j", "size": "20"},
    ],
    "19-35": [
        {"name": "1", "size": "22D"},
        {"name": "2", "size": "22D"},
        {"name": "3", "size": "22D"},
        {"name": "4", "size": "22D"},
        {"name": "5", "size": "22D"},
        {"name": "6", "size": "22D"},
        {"name": "7", "size": "22D"},
        {"name": "8", "size": "22D"},
        {"name": "9", "size": "22D"},
        {"name": "10", "size": "22D"},
        {"name": "11", "size": "22D"},
        {"name": "12", "size": "22D"},
        {"name": "13", "size": "22D"},
        {"name": "14", "size": "22D"},
        {"name": "15", "size": "22D"},
        {"name": "16", "size": "22D"},
        {"name": "17", "size": "22D"},
        {"name": "18", "size": "22D"},
        {"name": "19", "size": "22D"},
        {"name": "20", "size": "22D"},
        {"name": "21", "size": "22D"},
        {"name": "22", "size": "22D"},
        {"name": "23", "size": "22D"},
        {"name": "24", "size": "22D"},
        {"name": "25", "size": "22D"},
        {"name": "26", "size": "22D"},
        {"name": "27", "size": "22D"},
        {"name": "28", "size": "22D"},
        {"name": "29", "size": "22D"},
        {"name": "30", "size": "22D"},
        {"name": "31", "size": "22D"},
        {"name": "32", "size": "22D"},
        {"name": "33", "size": "22D"},
        {"name": "34", "size": "22D"},
        {"name": "35", "size": "22D"},
        {"name": "36", "size": "22D"},
        {"name": "37", "size": "22D"},
        {"name": "38", "size": "22D"},
        {"name": "39", "size": "22D"},
        {"name": "40", "size": "22D"},
        {"name": "41", "size": "22D"},
        {"name": "42", "size": "22D"},
        {"name": "43", "size": "22D"},
        {"name": "44", "size": "22D"},
        {"name": "45", "size": "22D"},
        {"name": "46", "size": "22D"},
        {"name": "47", "size": "22D"},
        {"name": "48", "size": "22D"},
        {"name": "49", "size": "22D"},
        {"name": "50", "size": "22D"},
        {"name": "51", "size": "22D"},
        {"name": "52", "size": "22D"},
        {"name": "53", "size": "22D"},
        {"name": "54", "size": "22D"},
        {"name": "55", "size": "22D"},
        {"name": "56", "size": "22D"},
        {"name": "57", "size": "22D"},
        {"name": "58", "size": "22D"},
        {"name": "59", "size": "22D"},
        {"name": "60", "size": "22D"},
        {"name": "61", "size": "22D"},
        {"name": "62", "size": "22D"},
        {"name": "63", "size": "22D"},
        {"name": "64", "size": "22D"},
        {"name": "65", "size": "22D"},
        {"name": "66", "size": "22D"},
    ],
    "21-11": [
        {"name": "A", "size": "12"},
        {"name": "B", "size": "12"},
        {"name": "C", "size": "12"},
        {"name": "D", "size": "12"},
        {"name": "E", "size": "12"},
        {"name": "F", "size": "12"},
        {"name": "G", "size": "12"},
        {"name": "H", "size": "12"},
        {"name": "J", "size": "12"},
        {"name": "K", "size": "12"},
        {"name": "L", "size": "12"},
    ],
    "21-16": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
        {"name": "C", "size": "16"},
        {"name": "D", "size": "16"},
        {"name": "E", "size": "16"},
        {"name": "F", "size": "16"},
        {"name": "G", "size": "16"},
        {"name": "H", "size": "16"},
        {"name": "J", "size": "16"},
        {"name": "K", "size": "16"},
        {"name": "L", "size": "16"},
        {"name": "M", "size": "16"},
        {"name": "N", "size": "16"},
        {"name": "P", "size": "12"},
        {"name": "R", "size": "16"},
        {"name": "S", "size": "16"},
    ],
    "21-29": [
        {"name": "1", "size": "20"},
        {"name": "2", "size": "20"},
        {"name": "3", "size": "20"},
        {"name": "4", "size": "20"},
        {"name": "5", "size": "20"},
        {"name": "6", "size": "20"},
        {"name": "7", "size": "20"},
        {"name": "8", "size": "20"},
        {"name": "9", "size": "20"},
        {"name": "10", "size": "20"},
        {"name": "11", "size": "20"},
        {"name": "12", "size": "20"},
        {"name": "13", "size": "20"},
        {"name": "14", "size": "20"},
        {"name": "15", "size": "20"},
        {"name": "16", "size": "20"},
        {"name": "17", "size": "20"},
        {"name": "18", "size": "20"},
        {"name": "19", "size": "20"},
        {"name": "20", "size": "12"},
        {"name": "21", "size": "16"},
        {"name": "22", "size": "12"},
        {"name": "23", "size": "12"},
        {"name": "24", "size": "16"},
        {"name": "25", "size": "12"},
        {"name": "26", "size": "16"},
        {"name": "27", "size": "16"},
    ],
    "21-35": [
        {"name": "1", "size": "22D"},
        {"name": "2", "size": "22D"},
        {"name": "3", "size": "22D"},
        {"name": "4", "size": "22D"},
        {"name": "5", "size": "22D"},
        {"name": "6", "size": "22D"},
        {"name": "7", "size": "22D"},
        {"name": "8", "size": "22D"},
        {"name": "9", "size": "22D"},
        {"name": "10", "size": "22D"},
        {"name": "11", "size": "22D"},
        {"name": "12", "size": "22D"},
        {"name": "13", "size": "22D"},
        {"name": "14", "size": "22D"},
        {"name": "15", "size": "22D"},
        {"name": "16", "size": "22D"},
        {"name": "17", "size": "22D"},
        {"name": "18", "size": "22D"},
        {"name": "19", "size": "22D"},
        {"name": "20", "size": "22D"},
        {"name": "21", "size": "22D"},
        {"name": "22", "size": "22D"},
        {"name": "23", "size": "22D"},
        {"name": "24", "size": "22D"},
        {"name": "25", "size": "22D"},
        {"name": "26", "size": "22D"},
        {"name": "27", "size": "22D"},
        {"name": "28", "size": "22D"},
        {"name": "29", "size": "22D"},
        {"name": "30", "size": "22D"},
        {"name": "31", "size": "22D"},
        {"name": "32", "size": "22D"},
        {"name": "33", "size": "22D"},
        {"name": "34", "size": "22D"},
        {"name": "35", "size": "22D"},
        {"name": "36", "size": "22D"},
        {"name": "37", "size": "22D"},
        {"name": "38", "size": "22D"},
        {"name": "39", "size": "22D"},
        {"name": "40", "size": "22D"},
        {"name": "41", "size": "22D"},
        {"name": "42", "size": "22D"},
        {"name": "43", "size": "22D"},
        {"name": "44", "size": "22D"},
        {"name": "45", "size": "22D"},
        {"name": "46", "size": "22D"},
        {"name": "47", "size": "22D"},
        {"name": "48", "size": "22D"},
        {"name": "49", "size": "22D"},
        {"name": "50", "size": "22D"},
        {"name": "51", "size": "22D"},
        {"name": "52", "size": "22D"},
        {"name": "53", "size": "22D"},
        {"name": "54", "size": "22D"},
        {"name": "55", "size": "22D"},
        {"name": "56", "size": "22D"},
        {"name": "57", "size": "22D"},
        {"name": "58", "size": "22D"},
        {"name": "59", "size": "22D"},
        {"name": "60", "size": "22D"},
        {"name": "61", "size": "22D"},
        {"name": "62", "size": "22D"},
        {"name": "63", "size": "22D"},
        {"name": "64", "size": "22D"},
        {"name": "65", "size": "22D"},
        {"name": "66", "size": "22D"},
        {"name": "67", "size": "22D"},
        {"name": "68", "size": "22D"},
        {"name": "69", "size": "22D"},
        {"name": "70", "size": "22D"},
        {"name": "71", "size": "22D"},
        {"name": "72", "size": "22D"},
        {"name": "73", "size": "22D"},
        {"name": "74", "size": "22D"},
        {"name": "75", "size": "22D"},
        {"name": "76", "size": "22D"},
        {"name": "77", "size": "22D"},
        {"name": "78", "size": "22D"},
        {"name": "79", "size": "22D"},
    ],
    "21-39": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "20"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "20"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "20"},
        {"name": "a", "size": "20"},
        {"name": "b", "size": "20"},
        {"name": "c", "size": "20"},
        {"name": "d", "size": "20"},
        {"name": "e", "size": "20"},
        {"name": "f", "size": "20"},
        {"name": "g", "size": "20"},
        {"name": "h", "size": "20"},
        {"name": "j", "size": "20"},
        {"name": "k", "size": "20"},
        {"name": "l", "size": "20"},
        {"name": "m", "size": "16"},
        {"name": "n", "size": "20"},
        {"name": "p", "size": "20"},
        {"name": "r", "size": "16"},
    ],
    "21-41": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "20"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "20"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "20"},
        {"name": "a", "size": "20"},
        {"name": "b", "size": "20"},
        {"name": "c", "size": "20"},
        {"name": "d", "size": "20"},
        {"name": "e", "size": "20"},
        {"name": "f", "size": "20"},
        {"name": "g", "size": "20"},
        {"name": "h", "size": "20"},
        {"name": "j", "size": "20"},
        {"name": "k", "size": "20"},
        {"name": "l", "size": "20"},
        {"name": "m", "size": "16"},
        {"name": "n", "size": "20"},
        {"name": "p", "size": "20"},
        {"name": "r", "size": "16"},
        {"name": "s", "size": "20"},
        {"name": "t", "size": "20"},
    ],
    "23-21": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
        {"name": "C", "size": "16"},
        {"name": "D", "size": "16"},
        {"name": "E", "size": "16"},
        {"name": "F", "size": "16"},
        {"name": "G", "size": "16"},
        {"name": "H", "size": "16"},
        {"name": "J", "size": "16"},
        {"name": "K", "size": "16"},
        {"name": "L", "size": "16"},
        {"name": "M", "size": "16"},
        {"name": "N", "size": "16"},
        {"name": "P", "size": "12"},
        {"name": "R", "size": "16"},
        {"name": "S", "size": "16"},
        {"name": "T", "size": "16"},
        {"name": "U", "size": "16"},
        {"name": "V", "size": "16"},
        {"name": "W", "size": "16"},
        {"name": "X", "size": "16"},
    ],
    "23-35": [
        {"name": "1", "size": "22D"},
        {"name": "2", "size": "22D"},
        {"name": "3", "size": "22D"},
        {"name": "4", "size": "22D"},
        {"name": "5", "size": "22D"},
        {"name": "6", "size": "22D"},
        {"name": "7", "size": "22D"},
        {"name": "8", "size": "22D"},
        {"name": "9", "size": "22D"},
        {"name": "10", "size": "22D"},
        {"name": "11", "size": "22D"},
        {"name": "12", "size": "22D"},
        {"name": "13", "size": "22D"},
        {"name": "14", "size": "22D"},
        {"name": "15", "size": "22D"},
        {"name": "16", "size": "22D"},
        {"name": "17", "size": "22D"},
        {"name": "18", "size": "22D"},
        {"name": "19", "size": "22D"},
        {"name": "20", "size": "22D"},
        {"name": "21", "size": "22D"},
        {"name": "22", "size": "22D"},
        {"name": "23", "size": "22D"},
        {"name": "24", "size": "22D"},
        {"name": "25", "size": "22D"},
        {"name": "26", "size": "22D"},
        {"name": "27", "size": "22D"},
        {"name": "28", "size": "22D"},
        {"name": "29", "size": "22D"},
        {"name": "30", "size": "22D"},
        {"name": "31", "size": "22D"},
        {"name": "32", "size": "22D"},
        {"name": "33", "size": "22D"},
        {"name": "34", "size": "22D"},
        {"name": "35", "size": "22D"},
        {"name": "36", "size": "22D"},
        {"name": "37", "size": "22D"},
        {"name": "38", "size": "22D"},
        {"name": "39", "size": "22D"},
        {"name": "40", "size": "22D"},
        {"name": "41", "size": "22D"},
        {"name": "42", "size": "22D"},
        {"name": "43", "size": "22D"},
        {"name": "44", "size": "22D"},
        {"name": "45", "size": "22D"},
        {"name": "46", "size": "22D"},
        {"name": "47", "size": "22D"},
        {"name": "48", "size": "22D"},
        {"name": "49", "size": "22D"},
        {"name": "50", "size": "22D"},
        {"name": "51", "size": "22D"},
        {"name": "52", "size": "22D"},
        {"name": "53", "size": "22D"},
        {"name": "54", "size": "22D"},
        {"name": "55", "size": "22D"},
        {"name": "56", "size": "22D"},
        {"name": "57", "size": "22D"},
        {"name": "58", "size": "22D"},
        {"name": "59", "size": "22D"},
        {"name": "60", "size": "22D"},
        {"name": "61", "size": "22D"},
        {"name": "62", "size": "22D"},
        {"name": "63", "size": "22D"},
        {"name": "64", "size": "22D"},
        {"name": "65", "size": "22D"},
        {"name": "66", "size": "22D"},
        {"name": "67", "size": "22D"},
        {"name": "68", "size": "22D"},
        {"name": "69", "size": "22D"},
        {"name": "70", "size": "22D"},
        {"name": "71", "size": "22D"},
        {"name": "72", "size": "22D"},
        {"name": "73", "size": "22D"},
        {"name": "74", "size": "22D"},
        {"name": "75", "size": "22D"},
        {"name": "76", "size": "22D"},
        {"name": "77", "size": "22D"},
        {"name": "78", "size": "22D"},
        {"name": "79", "size": "22D"},
        {"name": "80", "size": "22D"},
        {"name": "81", "size": "22D"},
        {"name": "82", "size": "22D"},
        {"name": "83", "size": "22D"},
        {"name": "84", "size": "22D"},
        {"name": "85", "size": "22D"},
        {"name": "86", "size": "22D"},
        {"name": "87", "size": "22D"},
        {"name": "88", "size": "22D"},
        {"name": "89", "size": "22D"},
        {"name": "90", "size": "22D"},
        {"name": "91", "size": "22D"},
        {"name": "92", "size": "22D"},
        {"name": "93", "size": "22D"},
        {"name": "94", "size": "22D"},
        {"name": "95", "size": "22D"},
        {"name": "96", "size": "22D"},
        {"name": "97", "size": "22D"},
        {"name": "98", "size": "22D"},
        {"name": "99", "size": "22D"},
        {"name": "100", "size": "22D"},
    ],
    "23-53": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "20"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "20"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "20"},
        {"name": "a", "size": "20"},
        {"name": "b", "size": "20"},
        {"name": "c", "size": "20"},
        {"name": "d", "size": "20"},
        {"name": "e", "size": "20"},
        {"name": "f", "size": "20"},
        {"name": "g", "size": "20"},
        {"name": "h", "size": "20"},
        {"name": "j", "size": "20"},
        {"name": "k", "size": "20"},
        {"name": "l", "size": "20"},
        {"name": "m", "size": "20"},
        {"name": "n", "size": "20"},
        {"name": "p", "size": "20"},
        {"name": "r", "size": "20"},
        {"name": "s", "size": "20"},
        {"name": "t", "size": "20"},
        {"name": "u", "size": "20"},
        {"name": "v", "size": "20"},
        {"name": "w", "size": "20"},
        {"name": "x", "size": "20"},
        {"name": "y", "size": "20"},
        {"name": "z", "size": "20"},
        {"name": "AA", "size": "20"},
        {"name": "BB", "size": "20"},
        {"name": "CC", "size": "20"},
        {"name": "DD", "size": "20"},
        {"name": "EE", "size": "20"},
        {"name": "FF", "size": "20"},
        {"name": "GG", "size": "20"},
        {"name": "HH", "size": "20"},
    ],
    "23-55": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "20"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "20"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "20"},
        {"name": "a", "size": "20"},
        {"name": "b", "size": "20"},
        {"name": "c", "size": "20"},
        {"name": "d", "size": "20"},
        {"name": "e", "size": "20"},
        {"name": "f", "size": "20"},
        {"name": "g", "size": "20"},
        {"name": "h", "size": "20"},
        {"name": "i", "size": "20"},
        {"name": "j", "size": "20"},
        {"name": "j", "size": "20"},
        {"name": "k", "size": "20"},
        {"name": "l", "size": "20"},
        {"name": "m", "size": "20"},
        {"name": "n", "size": "20"},
        {"name": "p", "size": "20"},
        {"name": "r", "size": "20"},
        {"name": "s", "size": "20"},
        {"name": "t", "size": "20"},
        {"name": "u", "size": "20"},
        {"name": "v", "size": "20"},
        {"name": "w", "size": "20"},
        {"name": "x", "size": "20"},
        {"name": "y", "size": "20"},
        {"name": "z", "size": "20"},
        {"name": "AA", "size": "20"},
        {"name": "BB", "size": "20"},
        {"name": "CC", "size": "20"},
        {"name": "DD", "size": "20"},
        {"name": "EE", "size": "20"},
        {"name": "FF", "size": "20"},
        {"name": "GG", "size": "20"},
        {"name": "HH", "size": "20"},
    ],
    "25-4": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "20"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "20"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "20"},
        {"name": "a", "size": "20"},
        {"name": "b", "size": "20"},
        {"name": "c", "size": "20"},
        {"name": "d", "size": "20"},
        {"name": "e", "size": "20"},
        {"name": "f", "size": "20"},
        {"name": "g", "size": "20"},
        {"name": "h", "size": "20"},
        {"name": "j", "size": "20"},
        {"name": "k", "size": "20"},
        {"name": "l", "size": "20"},
        {"name": "m", "size": "20"},
        {"name": "n", "size": "20"},
        {"name": "p", "size": "20"},
        {"name": "r", "size": "20"},
        {"name": "s", "size": "20"},
        {"name": "t", "size": "20"},
        {"name": "u", "size": "20"},
        {"name": "v", "size": "20"},
        {"name": "w", "size": "20"},
        {"name": "x", "size": "20"},
        {"name": "y", "size": "20"},
        {"name": "z", "size": "20"},
        {"name": "AA", "size": "20"},
        {"name": "BB", "size": "20"},
        {"name": "CC", "size": "20"},
        {"name": "DD", "size": "16"},
        {"name": "EE", "size": "16"},
        {"name": "FF", "size": "16"},
        {"name": "GG", "size": "16"},
        {"name": "HH", "size": "16"},
        {"name": "JJ", "size": "16"},
        {"name": "KK", "size": "20"},
        {"name": "LL", "size": "16"},
    ],
    "25-19": [
        {"name": "A", "size": "12"},
        {"name": "B", "size": "12"},
        {"name": "C", "size": "12"},
        {"name": "D", "size": "12"},
        {"name": "E", "size": "12"},
        {"name": "F", "size": "12"},
        {"name": "G", "size": "12"},
        {"name": "H", "size": "12"},
        {"name": "J", "size": "12"},
        {"name": "K", "size": "12"},
        {"name": "L", "size": "12"},
        {"name": "M", "size": "12"},
        {"name": "N", "size": "12"},
        {"name": "P", "size": "12"},
        {"name": "R", "size": "12"},
        {"name": "S", "size": "12"},
        {"name": "T", "size": "12"},
        {"name": "U", "size": "12"},
        {"name": "V", "size": "12"},
    ],
    "25-29": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
        {"name": "C", "size": "16"},
        {"name": "D", "size": "16"},
        {"name": "E", "size": "16"},
        {"name": "F", "size": "16"},
        {"name": "G", "size": "16"},
        {"name": "H", "size": "16"},
        {"name": "J", "size": "16"},
        {"name": "K", "size": "16"},
        {"name": "L", "size": "16"},
        {"name": "M", "size": "16"},
        {"name": "N", "size": "16"},
        {"name": "P", "size": "12"},
        {"name": "R", "size": "16"},
        {"name": "S", "size": "16"},
        {"name": "T", "size": "16"},
        {"name": "U", "size": "16"},
        {"name": "V", "size": "16"},
        {"name": "W", "size": "16"},
        {"name": "X", "size": "16"},
        {"name": "Y", "size": "16"},
        {"name": "Z", "size": "16"},
        {"name": "a", "size": "16"},
        {"name": "b", "size": "16"},
        {"name": "c", "size": "16"},
        {"name": "d", "size": "16"},
        {"name": "e", "size": "16"},
        {"name": "f", "size": "16"},
    ],
    "25-35": [
        {"name": "1", "size": "22D"},
        {"name": "2", "size": "22D"},
        {"name": "3", "size": "22D"},
        {"name": "4", "size": "22D"},
        {"name": "5", "size": "22D"},
        {"name": "6", "size": "22D"},
        {"name": "7", "size": "22D"},
        {"name": "8", "size": "22D"},
        {"name": "9", "size": "22D"},
        {"name": "10", "size": "22D"},
        {"name": "11", "size": "22D"},
        {"name": "12", "size": "22D"},
        {"name": "13", "size": "22D"},
        {"name": "14", "size": "22D"},
        {"name": "15", "size": "22D"},
        {"name": "16", "size": "22D"},
        {"name": "17", "size": "22D"},
        {"name": "18", "size": "22D"},
        {"name": "19", "size": "22D"},
        {"name": "20", "size": "22D"},
        {"name": "21", "size": "22D"},
        {"name": "22", "size": "22D"},
        {"name": "23", "size": "22D"},
        {"name": "24", "size": "22D"},
        {"name": "25", "size": "22D"},
        {"name": "26", "size": "22D"},
        {"name": "27", "size": "22D"},
        {"name": "28", "size": "22D"},
        {"name": "29", "size": "22D"},
        {"name": "30", "size": "22D"},
        {"name": "31", "size": "22D"},
        {"name": "32", "size": "22D"},
        {"name": "33", "size": "22D"},
        {"name": "34", "size": "22D"},
        {"name": "35", "size": "22D"},
        {"name": "36", "size": "22D"},
        {"name": "37", "size": "22D"},
        {"name": "38", "size": "22D"},
        {"name": "39", "size": "22D"},
        {"name": "40", "size": "22D"},
        {"name": "41", "size": "22D"},
        {"name": "42", "size": "22D"},
        {"name": "43", "size": "22D"},
        {"name": "44", "size": "22D"},
        {"name": "45", "size": "22D"},
        {"name": "46", "size": "22D"},
        {"name": "47", "size": "22D"},
        {"name": "48", "size": "22D"},
        {"name": "49", "size": "22D"},
        {"name": "50", "size": "22D"},
        {"name": "51", "size": "22D"},
        {"name": "52", "size": "22D"},
        {"name": "53", "size": "22D"},
        {"name": "54", "size": "22D"},
        {"name": "55", "size": "22D"},
        {"name": "56", "size": "22D"},
        {"name": "57", "size": "22D"},
        {"name": "58", "size": "22D"},
        {"name": "59", "size": "22D"},
        {"name": "60", "size": "22D"},
        {"name": "61", "size": "22D"},
        {"name": "62", "size": "22D"},
        {"name": "63", "size": "22D"},
        {"name": "64", "size": "22D"},
        {"name": "65", "size": "22D"},
        {"name": "66", "size": "22D"},
        {"name": "67", "size": "22D"},
        {"name": "68", "size": "22D"},
        {"name": "69", "size": "22D"},
        {"name": "70", "size": "22D"},
        {"name": "71", "size": "22D"},
        {"name": "72", "size": "22D"},
        {"name": "73", "size": "22D"},
        {"name": "74", "size": "22D"},
        {"name": "75", "size": "22D"},
        {"name": "76", "size": "22D"},
        {"name": "77", "size": "22D"},
        {"name": "78", "size": "22D"},
        {"name": "79", "size": "22D"},
        {"name": "80", "size": "22D"},
        {"name": "81", "size": "22D"},
        {"name": "82", "size": "22D"},
        {"name": "83", "size": "22D"},
        {"name": "84", "size": "22D"},
        {"name": "85", "size": "22D"},
        {"name": "86", "size": "22D"},
        {"name": "87", "size": "22D"},
        {"name": "88", "size": "22D"},
        {"name": "89", "size": "22D"},
        {"name": "90", "size": "22D"},
        {"name": "91", "size": "22D"},
        {"name": "92", "size": "22D"},
        {"name": "93", "size": "22D"},
        {"name": "94", "size": "22D"},
        {"name": "95", "size": "22D"},
        {"name": "96", "size": "22D"},
        {"name": "97", "size": "22D"},
        {"name": "98", "size": "22D"},
        {"name": "99", "size": "22D"},
        {"name": "100", "size": "22D"},
        {"name": "101", "size": "22D"},
        {"name": "102", "size": "22D"},
        {"name": "103", "size": "22D"},
        {"name": "104", "size": "22D"},
        {"name": "105", "size": "22D"},
        {"name": "106", "size": "22D"},
        {"name": "107", "size": "22D"},
        {"name": "108", "size": "22D"},
        {"name": "109", "size": "22D"},
        {"name": "110", "size": "22D"},
        {"name": "111", "size": "22D"},
        {"name": "112", "size": "22D"},
        {"name": "113", "size": "22D"},
        {"name": "114", "size": "22D"},
        {"name": "115", "size": "22D"},
        {"name": "116", "size": "22D"},
        {"name": "117", "size": "22D"},
        {"name": "118", "size": "22D"},
        {"name": "119", "size": "22D"},
        {"name": "120", "size": "22D"},
        {"name": "121", "size": "22D"},
        {"name": "122", "size": "22D"},
        {"name": "123", "size": "22D"},
        {"name": "124", "size": "22D"},
        {"name": "125", "size": "22D"},
        {"name": "126", "size": "22D"},
        {"name": "127", "size": "22D"},
        {"name": "128", "size": "22D"},
    ],
    "25-37": [
        {"name": "A", "size": "16"},
        {"name": "B", "size": "16"},
        {"name": "C", "size": "16"},
        {"name": "D", "size": "16"},
        {"name": "E", "size": "16"},
        {"name": "F", "size": "16"},
        {"name": "G", "size": "16"},
        {"name": "H", "size": "16"},
        {"name": "J", "size": "16"},
        {"name": "K", "size": "16"},
        {"name": "L", "size": "16"},
        {"name": "M", "size": "16"},
        {"name": "N", "size": "16"},
        {"name": "P", "size": "12"},
        {"name": "R", "size": "16"},
        {"name": "S", "size": "16"},
        {"name": "T", "size": "16"},
        {"name": "U", "size": "16"},
        {"name": "V", "size": "16"},
        {"name": "W", "size": "16"},
        {"name": "X", "size": "16"},
        {"name": "Y", "size": "16"},
        {"name": "Z", "size": "16"},
        {"name": "a", "size": "16"},
        {"name": "b", "size": "16"},
        {"name": "c", "size": "16"},
        {"name": "d", "size": "16"},
        {"name": "e", "size": "16"},
        {"name": "f", "size": "16"},
        {"name": "g", "size": "16"},
        {"name": "h", "size": "16"},
        {"name": "k", "size": "16"},
        {"name": "l", "size": "16"},
        {"name": "m", "size": "16"},
        {"name": "n", "size": "16"},
        {"name": "p", "size": "12"},
        {"name": "r", "size": "16"},
    ],
    "25-61": [
        {"name": "A", "size": "20"},
        {"name": "B", "size": "20"},
        {"name": "C", "size": "20"},
        {"name": "D", "size": "20"},
        {"name": "E", "size": "20"},
        {"name": "F", "size": "20"},
        {"name": "G", "size": "20"},
        {"name": "H", "size": "20"},
        {"name": "J", "size": "20"},
        {"name": "K", "size": "20"},
        {"name": "L", "size": "20"},
        {"name": "M", "size": "20"},
        {"name": "N", "size": "20"},
        {"name": "P", "size": "16"},
        {"name": "R", "size": "20"},
        {"name": "S", "size": "20"},
        {"name": "T", "size": "20"},
        {"name": "U", "size": "20"},
        {"name": "V", "size": "20"},
        {"name": "W", "size": "20"},
        {"name": "X", "size": "20"},
        {"name": "Y", "size": "20"},
        {"name": "Z", "size": "20"},
        {"name": "a", "size": "20"},
        {"name": "b", "size": "20"},
        {"name": "c", "size": "20"},
        {"name": "d", "size": "20"},
        {"name": "e", "size": "20"},
        {"name": "f", "size": "20"},
        {"name": "g", "size": "20"},
        {"name": "h", "size": "20"},
        {"name": "i", "size": "20"},
        {"name": "j", "size": "20"},
        {"name": "k", "size": "20"},
        {"name": "l", "size": "20"},
        {"name": "m", "size": "20"},
        {"name": "n", "size": "20"},
        {"name": "p", "size": "16"},
        {"name": "r", "size": "20"},
        {"name": "s", "size": "20"},
        {"name": "t", "size": "20"},
        {"name": "u", "size": "20"},
        {"name": "v", "size": "20"},
        {"name": "w", "size": "20"},
        {"name": "x", "size": "20"},
        {"name": "y", "size": "20"},
        {"name": "z", "size": "20"},
        {"name": "AA", "size": "20"},
        {"name": "BB", "size": "20"},
        {"name": "CC", "size": "20"},
        {"name": "DD", "size": "20"},
        {"name": "EE", "size": "20"},
        {"name": "FF", "size": "20"},
        {"name": "GG", "size": "20"},
        {"name": "HH", "size": "20"},
        {"name": "JJ", "size": "20"},
        {"name": "KK", "size": "20"},
        {"name": "LL", "size": "20"},
        {"name": "MM", "size": "20"},
        {"name": "NN", "size": "20"},
        {"name": "PP", "size": "20"},
    ]
}

# Polar flagnotes about the drawing origin. Leader tips are the ray–perimeter
# hit for that shell (see flagnote_csys_children). Flag bodies stay at 3 in.
FLAGNOTE_ANGLES_DEG = [0, 15, -15, 30, -30, 45, -45, 60, -60, -75, 75, -90, 90]
FLAGNOTE_RADIUS_IN = 3.0

# Approximate drawing colors from MIL-DTL-38999 Series III material/finish photos:
# https://d38999.federalconnectors.com/
FINISH_DRAWING_COLORS = {
    "F": {  # Aluminum, electroless nickel — bright chrome-like silver
        "body": "#C5CAD0",
        "light": "#E6EAEF",
        "dark": "#8E959C",
        "rim": "#6E747A",
        "knurl": "#6A7178",
    },
    "G": {  # Aluminum, space-grade electroless nickel — satin silver
        "body": "#B4B9BE",
        "light": "#D4D8DC",
        "dark": "#8A9096",
        "rim": "#6A7076",
        "knurl": "#676D73",
    },
    "J": {  # Composite, olive drab cadmium — dark muted olive
        "body": "#3F412E",
        "light": "#555740",
        "dark": "#2A2C1E",
        "rim": "#1E2016",
        "knurl": "#5A5C44",
    },
    "K": {  # Stainless steel, passivated — flatter medium grey
        "body": "#A3A4A0",
        "light": "#C0C1BD",
        "dark": "#7A7B77",
        "rim": "#5E5F5B",
        "knurl": "#5C5D59",
    },
    "L": {  # Stainless steel, electrodeposited nickel
        "body": "#C0C4C8",
        "light": "#DEE2E6",
        "dark": "#8C9196",
        "rim": "#6E7378",
        "knurl": "#6A6F74",
    },
    "M": {  # Composite, electroless nickel — similar to F
        "body": "#C5CAD0",
        "light": "#E6EAEF",
        "dark": "#8E959C",
        "rim": "#6E747A",
        "knurl": "#6A7178",
    },
    "S": {  # Stainless steel, nickel plated
        "body": "#C0C4C8",
        "light": "#DEE2E6",
        "dark": "#8C9196",
        "rim": "#6E7378",
        "knurl": "#6A6F74",
    },
    "T": {  # Aluminum, nickel PTFE — duller grey metallic
        "body": "#9B9E9A",
        "light": "#B5B8B4",
        "dark": "#6F726E",
        "rim": "#555855",
        "knurl": "#525551",
    },
    "W": {  # Aluminum, olive drab cadmium — khaki / greenish-bronze
        "body": "#6F703C",
        "light": "#8C8D55",
        "dark": "#4A4B28",
        "rim": "#3A3B20",
        "knurl": "#2E3018",
    },
    "Y": {  # Hermetic stainless, passivated
        "body": "#A3A4A0",
        "light": "#C0C1BD",
        "dark": "#7A7B77",
        "rim": "#5E5F5B",
        "knurl": "#5C5D59",
    },
    "Z": {  # Aluminum, black zinc nickel — deep charcoal
        "body": "#3D3E40",
        "light": "#555658",
        "dark": "#262728",
        "rim": "#141516",
        "knurl": "#6A6B6D",
    },
}
_DEFAULT_FINISH_COLORS = {
    "body": "#C0C0C0",
    "light": "#D8D8D8",
    "dark": "#A8A8A8",
    "rim": "#444444",
    "knurl": "#555555",
}

# SVG px per inch — must match harnice part.py csys rendering (96 px/in)
PX_PER_IN = 96.0
MM_PER_IN = 25.4
STROKE_COLOR = "#222222"
STROKE_WIDTH = 1.5
SEAL_COLOR = "#1A1A1A"
# Origin is this far inboard of the rear accessory face; threads overlap −X.
ORIGIN_FROM_REAR_IN = 0.25


def finish_palette(finish):
    return {**_DEFAULT_FINISH_COLORS, **FINISH_DRAWING_COLORS.get((finish or "").upper(), {})}


def px_mm(mm):
    return mm / MM_PER_IN * PX_PER_IN


def px_in(inches):
    return inches * PX_PER_IN


def _stroke_attr(stroke, stroke_width):
    if stroke is None:
        return ' stroke="none"'
    return f' stroke="{stroke}" stroke-width="{stroke_width}"'


def _rect(x, y, w, h, fill="#C0C0C0", stroke=STROKE_COLOR, stroke_width=STROKE_WIDTH):
    return (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'fill="{fill}"{_stroke_attr(stroke, stroke_width)}/>'
    )


def _poly(points, fill="#C0C0C0", stroke=STROKE_COLOR, stroke_width=STROKE_WIDTH):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return (
        f'<polygon points="{pts}" fill="{fill}"'
        f'{_stroke_attr(stroke, stroke_width)}/>'
    )


def _line(x1, y1, x2, y2, stroke=STROKE_COLOR, stroke_width=1.0):
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )


def _clip_seg(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    """Liang–Barsky clip of a segment to an axis-aligned rectangle."""
    dx = x2 - x1
    dy = y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in (
        (-dx, x1 - xmin),
        (dx, xmax - x1),
        (-dy, y1 - ymin),
        (dy, ymax - y1),
    ):
        if p == 0.0:
            if q < 0.0:
                return None
            continue
        r = q / p
        if p < 0.0:
            if r > t1:
                return None
            if r > t0:
                t0 = r
        else:
            if r < t0:
                return None
            if r < t1:
                t1 = r
    return (x1 + t0 * dx, y1 + t0 * dy, x1 + t1 * dx, y1 + t1 * dy)


def _diamond_hatch(x, y, w, h, color, spacing=6.5, stroke_width=0.85):
    """Diamond knurl as clipped <line> segments (Harnice paints lines, not patterns)."""
    if w <= 0.5 or h <= 0.5:
        return []
    left, right = x, x + w
    top, bot = y, y + h
    lines = []

    def emit(ax, ay, bx, by):
        clipped = _clip_seg(ax, ay, bx, by, left, top, right, bot)
        if clipped is None:
            return
        x1, y1, x2, y2 = clipped
        if abs(x2 - x1) < 0.15 and abs(y2 - y1) < 0.15:
            return
        lines.append(_line(x1, y1, x2, y2, stroke=color, stroke_width=stroke_width))

    c = left - bot
    c_max = right - top
    while c <= c_max + 1e-6:
        emit(left, left - c, right, right - c)
        c += spacing
    c = left + top
    c_max = right + bot
    while c <= c_max + 1e-6:
        emit(left, c - left, right, c - right)
        c += spacing
    return lines


# ---------------------------------------------------------------------------
# Envelope / drawing dimensions — D38999/26 (Series III plug)
# ---------------------------------------------------------------------------
# Coupling nut ØDD and rear-body ØCC:
#   Glenair D38999/26 (MIL-DTL-38999 Series III environmental plug)
#   https://www.glenair.com/mil-dtl-38999-connector-series-iii/pdf/mil-dtl-38999-series-iii-environmental/d38999-26.pdf
# Overall length L max 31.34 mm (1.234 in), matching the existing 2D drawing:
#   Amphenol TV06 / Milnec TX06 (D38999/26 equivalents)
#   https://www.milnec.com/mil-38999-sst/d38999-26-sst-datasheet.pdf
# Origin is 0.25 in inboard of the rear accessory face, on the axis, so the
# accessory threads overlap −X (same idea as the M85049 banding platform).
# +X toward the mating face. STEP omits knurl texture.
SHELL_ENVELOPE_MM = {
    "A": {"cc": 18.60, "dd": 21.79, "q_max": 21.8, "length": 31.34, "numeric": 9},
    "B": {"cc": 21.30, "dd": 24.99, "q_max": 25.0, "length": 31.34, "numeric": 11},
    "C": {"cc": 25.60, "dd": 29.39, "q_max": 29.4, "length": 31.34, "numeric": 13},
    "D": {"cc": 28.90, "dd": 32.51, "q_max": 32.5, "length": 31.34, "numeric": 15},
    "E": {"cc": 32.40, "dd": 35.71, "q_max": 35.7, "length": 31.34, "numeric": 17},
    "F": {"cc": 35.10, "dd": 38.51, "q_max": 38.5, "length": 31.34, "numeric": 19},
    "G": {"cc": 38.30, "dd": 41.71, "q_max": 41.7, "length": 31.34, "numeric": 21},
    "H": {"cc": 41.30, "dd": 44.91, "q_max": 44.9, "length": 31.34, "numeric": 23},
    "J": {"cc": 44.50, "dd": 48.01, "q_max": 48.0, "length": 31.34, "numeric": 25},
}
COUPLING_NUT_LENGTH_MM = 16.0

# ---------------------------------------------------------------------------
# Envelope / drawing dimensions — D38999/24 (Series III jam-nut receptacle)
# ---------------------------------------------------------------------------
# Overall length L max 1.280 in (32.51 mm); K max 0.890 in (22.61 mm) from
# mating face to the jam-nut/panel shoulder:
#   Glenair D38999/24 (MIL-DTL-38999 Series III jam-nut receptacle)
#   https://www.glenair.com/mil-dtl-38999-connector-series-iii/pdf/mil-dtl-38999-series-iii-environmental/d38999-24.pdf
# Rear body Ø (Amphenol A) and jam-nut Ø (Glenair ØU max / Amphenol C max):
#   Amphenol TV07 / Milnec TX07 (D38999/24 equivalents)
#   https://www.milnec.com/mil-d38999-connectors/d38999-24-datasheet.pdf
# Jam-nut thickness is not tabulated; 0.220 in is a drawing estimate.
# Origin is 0.25 in inboard of the rear accessory face; +X toward the mating
# face. STEP is a smooth revolved envelope (hex becomes ØU).
JAM24_LENGTH_MM = 32.51
JAM24_K_MM = 22.61
JAM24_NUT_LENGTH_MM = 5.59
FULLY_MATED_RED = "#B91C1C"
SHELL_24_ENVELOPE_MM = {
    "A": {"body": 16.99, "nut": 30.51, "numeric": 9},
    "B": {"body": 19.53, "nut": 35.20, "numeric": 11},
    "C": {"body": 24.26, "nut": 38.40, "numeric": 13},
    "D": {"body": 27.53, "nut": 41.61, "numeric": 15},
    "E": {"body": 30.68, "nut": 44.81, "numeric": 17},
    "F": {"body": 33.86, "nut": 49.50, "numeric": 19},
    "G": {"body": 37.06, "nut": 52.71, "numeric": 21},
    "H": {"body": 40.01, "nut": 55.91, "numeric": 23},
    "J": {"body": 43.41, "nut": 59.00, "numeric": 25},
}

INSERT_ARRANGEMENT_CODES = [
    "A35",
    "A98",
    "B5",
    "B35",
    "B99",
    "C35",
    "C98",
    "D5",
    "D19",
    "D35",
    "E6",
    "E8",
    "E26",
    "E35",
    "F11",
    "F32",
    "F35",
    "G11",
    "G16",
    "G35",
    "G41",
    "H21",
    "H35",
    "H55",
    "J19",
    "J29",
    "J35",
    "J61",
]


def series_iii_26_envelope_stations(shell_size):
    """Stepped cylinder stations (x_mm, radius_mm) for a D38999/26 plug."""
    if shell_size not in SHELL_ENVELOPE_MM:
        raise ValueError(f"Shell size must be one of {list(SHELL_ENVELOPE_MM)}")
    spec = SHELL_ENVELOPE_MM[shell_size]
    length = spec["length"]
    nut = min(COUPLING_NUT_LENGTH_MM, length * 0.65)
    rear = -ORIGIN_FROM_REAR_IN * MM_PER_IN
    body_end = rear + (length - nut)
    face = rear + length
    r_body = spec["cc"] / 2.0
    r_nut = spec["dd"] / 2.0
    return [
        (rear, r_body),
        (body_end, r_body),
        (body_end, r_nut),
        (face, r_nut),
    ]


def series_iii_24_envelope_stations(shell_size):
    """Stepped cylinder stations (x_mm, radius_mm) for a D38999/24 jam-nut receptacle."""
    if shell_size not in SHELL_24_ENVELOPE_MM:
        raise ValueError(f"Shell size must be one of {list(SHELL_24_ENVELOPE_MM)}")
    spec = SHELL_24_ENVELOPE_MM[shell_size]
    rear = -ORIGIN_FROM_REAR_IN * MM_PER_IN
    face = rear + JAM24_LENGTH_MM
    nut_start = face - JAM24_K_MM
    nut_end = nut_start + JAM24_NUT_LENGTH_MM
    r_body = spec["body"] / 2.0
    r_nut = spec["nut"] / 2.0
    return [
        (rear, r_body),
        (nut_start, r_body),
        (nut_start, r_nut),
        (nut_end, r_nut),
        (nut_end, r_body),
        (face, r_body),
    ]


def envelope_stations(shell_type, shell_size):
    if shell_type == "24":
        return series_iii_24_envelope_stations(shell_size)
    if shell_type == "26":
        return series_iii_26_envelope_stations(shell_size)
    raise ValueError(f"Unsupported shell type '{shell_type}'")


def silhouette_closed_mm(stations):
    """Closed CCW outline (x, y) mm from revolution stations."""
    pts = [(x, r) for x, r in stations]
    pts += [(x, -r) for x, r in reversed(stations)]
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


def part_perimeter_inches(shell_type, shell_size):
    """Outer silhouette vertices in inches (math coords, +Y up), CCW, closed.

    Same stepped outline as the SVG / STEP envelope so leader tips land on the
    visible edge.
    """
    return [
        (x / MM_PER_IN, y / MM_PER_IN)
        for x, y in silhouette_closed_mm(envelope_stations(shell_type, shell_size))
    ]


def _ray_edge_intersection_t(origin, angle_rad, p0, p1, eps=1e-9):
    """Distance t>=0 along ray from origin at angle_rad to segment p0→p1, or None."""
    ox, oy = origin
    dx, dy = math.cos(angle_rad), math.sin(angle_rad)
    ex, ey = p1[0] - p0[0], p1[1] - p0[1]
    det = dx * ey - dy * ex
    if abs(det) < eps:
        return None
    rx, ry = p0[0] - ox, p0[1] - oy
    t = (rx * ey - ry * ex) / det
    u = (rx * dy - ry * dx) / det
    if t < -eps or u < -eps or u > 1 + eps:
        return None
    return max(0.0, t)


def _ray_perimeter_exit_distance(origin, angle_deg, perimeter):
    """Farthest intersection of a polar ray with the part perimeter (inches)."""
    if perimeter[0] != perimeter[-1]:
        perimeter = perimeter + [perimeter[0]]
    angle_rad = math.radians(angle_deg)
    hits = []
    for i in range(len(perimeter) - 1):
        t = _ray_edge_intersection_t(origin, angle_rad, perimeter[i], perimeter[i + 1])
        if t is not None and t > 1e-6:
            hits.append(t)
    if not hits:
        return None
    return max(hits)


def flagnote_csys_children(shell_type, shell_size):
    """Polar flagnotes about the origin; leaders at the silhouette exit."""
    perimeter = part_perimeter_inches(shell_type, shell_size)
    origin = (0.0, 0.0)
    children = {}
    for i, angle in enumerate(FLAGNOTE_ANGLES_DEG, start=1):
        r_leader = _ray_perimeter_exit_distance(origin, angle, perimeter)
        if r_leader is None:
            raise ValueError(
                f"flagnote-{i} ray at {angle}° does not hit the D38999/{shell_type} "
                f"shell {shell_size} perimeter"
            )
        children[f"flagnote-{i}"] = {
            "angle": angle,
            "distance": FLAGNOTE_RADIUS_IN,
            "rotation": 0,
        }
        children[f"flagnote-{i}-leader_dest"] = {
            "angle": angle,
            "distance": round(r_leader, 4),
            "rotation": 0,
        }
    return children


def _csys_overlay_svg(csys_children):
    """Harnice-style csys markers (96 px/in, +Y up stored as SVG −Y)."""
    arrow_len = 24
    dot_radius = 4
    arrow_size = 6
    lines = ['  <g id="output csys locations">']
    for csys_name, csys in csys_children.items():
        x = float(csys.get("x", 0)) * PX_PER_IN
        y = float(csys.get("y", 0)) * PX_PER_IN
        angle_rad = math.radians(float(csys.get("angle", 0)))
        dist_px = float(csys.get("distance", 0)) * PX_PER_IN
        x += dist_px * math.cos(angle_rad)
        y += dist_px * math.sin(angle_rad)
        rotation_rad = math.radians(float(csys.get("rotation", 0)))
        cos_r, sin_r = math.cos(rotation_rad), math.sin(rotation_rad)
        dx_x, dy_x = arrow_len * cos_r, arrow_len * sin_r
        dx_y, dy_y = -arrow_len * sin_r, arrow_len * cos_r

        def arrow(x1, y1, dx, dy, color):
            x2, y2 = x1 + dx, y1 + dy
            length = math.hypot(dx, dy)
            ux, uy = dx / length, dy / length
            px, py = -uy, ux
            base_x = x2 - ux * arrow_size
            base_y = y2 - uy * arrow_size
            return [
                f'      <line x1="{x1:.2f}" y1="{-y1:.2f}" x2="{x2:.2f}" y2="{-y2:.2f}" '
                f'stroke="{color}" stroke-width="2"/>',
                f'      <polygon points="{x2:.2f},{-y2:.2f} '
                f'{base_x + px * arrow_size / 2:.2f},{-(base_y + py * arrow_size / 2):.2f} '
                f'{base_x - px * arrow_size / 2:.2f},{-(base_y - py * arrow_size / 2):.2f}" '
                f'fill="{color}"/>',
            ]

        lines.append(f'    <g id="{csys_name}">')
        lines.append(
            f'      <circle cx="{x:.2f}" cy="{-y:.2f}" r="{dot_radius}" fill="black"/>'
        )
        lines.extend(arrow(x, y, dx_x, dy_x, "red"))
        lines.extend(arrow(x, y, dx_y, dy_y, "green"))
        lines.append("    </g>")
    lines.append("  </g>")
    return "\n".join(lines)


def write_part_step(rev_dir, part_number, shell_type, shell_size):
    path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-model.step")
    step_utils.write_revolution_step(
        path,
        part_number,
        envelope_stations(shell_type, shell_size),
        description=f"D38999/{shell_type} low-fidelity envelope",
    )
    return path


def series_iii_26_connector_svg(part_number, shell_size, finish=None):
    """Side-view D38999/26 plug. Origin 0.25 in inboard of the rear face; +X to the mating face.

    Silhouette matches the STEP envelope (Glenair ØCC rear body, ØDD coupling nut,
    L = 31.34 mm). Accessory threads overlap −X. 2D-only: diamond knurl, ratchet
    rim, interfacial seal.
    """
    if shell_size not in SHELL_ENVELOPE_MM:
        raise ValueError(f"Shell size must be one of {list(SHELL_ENVELOPE_MM)}")

    spec = SHELL_ENVELOPE_MM[shell_size]
    pal = finish_palette(finish)
    length = px_mm(spec["length"])
    nut_len = px_mm(min(COUPLING_NUT_LENGTH_MM, spec["length"] * 0.65))
    body_len = length - nut_len
    r_body = px_mm(spec["cc"] / 2.0)
    r_nut = px_mm(spec["dd"] / 2.0)
    x_rear = -px_in(ORIGIN_FROM_REAR_IN)
    x_nut = x_rear + body_len
    x_face = x_rear + length

    ratchet_w = min(px_mm(2.2), nut_len * 0.14)
    front_rim_w = min(px_mm(3.2), nut_len * 0.20)
    seal_w = min(px_mm(1.2), nut_len * 0.08)
    knurl_x = x_nut + ratchet_w
    knurl_w = max(0.0, nut_len - ratchet_w - front_rim_w)
    groove_x = x_face - front_rim_w

    outline = [
        (x_rear, -r_body),
        (x_nut, -r_body),
        (x_nut, -r_nut),
        (x_face, -r_nut),
        (x_face, r_nut),
        (x_nut, r_nut),
        (x_nut, r_body),
        (x_rear, r_body),
    ]

    parts = [
        "<!-- Finish colors approximated from https://d38999.federalconnectors.com/ -->",
        "<!-- Plug details from typical D38999/26 / Glenair 233-105 hardware -->",
        _rect(x_rear, -r_body, body_len, 2.0 * r_body, fill=pal["body"], stroke=None),
        _rect(x_nut, -r_nut, nut_len, 2.0 * r_nut, fill=pal["dark"], stroke=None),
        _rect(x_nut, -r_nut, ratchet_w, 2.0 * r_nut, fill=pal["rim"], stroke=None),
        _rect(groove_x, -r_nut, px_mm(0.6), 2.0 * r_nut, fill=pal["rim"], stroke=None),
        _rect(x_face - seal_w, -r_nut, seal_w, 2.0 * r_nut, fill=SEAL_COLOR, stroke=None),
    ]

    parts.extend(_diamond_hatch(knurl_x, -r_nut, knurl_w, 2.0 * r_nut, pal["knurl"]))

    n_ratchet = max(5, int(round(ratchet_w / 3.2)))
    tick = max(2.2, r_nut * 0.10)
    for i in range(n_ratchet):
        xx = x_nut + (i + 0.5) * ratchet_w / n_ratchet
        parts.append(_line(xx, -r_nut, xx, -r_nut + tick, stroke=pal["knurl"], stroke_width=0.8))
        parts.append(_line(xx, r_nut, xx, r_nut - tick, stroke=pal["knurl"], stroke_width=0.8))

    parts.append(_poly(outline, fill="none"))
    csys = flagnote_csys_children("26", shell_size)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="400" height="400">
<g id="{part_number}-drawing-contents-start">
{chr(10).join(parts)}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
{_csys_overlay_svg(csys)}
</svg>'''


def series_iii_24_connector_svg(part_number, shell_size, finish=None):
    """Side-view D38999/24 jam-nut receptacle.

    Origin 0.25 in inboard of the rear accessory face; +X to the mating face.
    Silhouette matches the STEP envelope: rear body (Amphenol A), jam nut
    (Glenair ØU), front mating barrel, L = 32.51 mm. 2D-only: fully-mated
    red band.
    """
    if shell_size not in SHELL_24_ENVELOPE_MM:
        raise ValueError(f"Shell size must be one of {list(SHELL_24_ENVELOPE_MM)}")

    pal = finish_palette(finish)
    stations = series_iii_24_envelope_stations(shell_size)
    x_rear = px_mm(stations[0][0])
    r_body = px_mm(stations[0][1])
    x_nut0 = px_mm(stations[1][0])
    r_nut = px_mm(stations[2][1])
    x_nut1 = px_mm(stations[3][0])
    x_face = px_mm(stations[5][0])
    body_len = x_nut0 - x_rear
    nut_len = x_nut1 - x_nut0
    front_len = x_face - x_nut1
    band_w = min(px_mm(1.6), front_len * 0.12)
    seal_w = min(px_mm(1.2), front_len * 0.08)
    outline = [(px_mm(x), px_mm(y)) for x, y in silhouette_closed_mm(stations)[:-1]]

    parts = [
        "<!-- Finish colors approximated from https://d38999.federalconnectors.com/ -->",
        "<!-- Jam-nut details from Glenair D38999/24 / Amphenol TV07 / Milnec TX07 -->",
        _rect(x_rear, -r_body, body_len, 2.0 * r_body, fill=pal["body"], stroke=None),
        _rect(x_nut1, -r_body, front_len, 2.0 * r_body, fill=pal["body"], stroke=None),
        _rect(x_nut0, -r_nut, nut_len, 2.0 * r_nut, fill=pal["dark"], stroke=None),
        _rect(x_face - front_len * 0.22, -r_body, band_w, 2.0 * r_body, fill=FULLY_MATED_RED, stroke=None),
        _rect(x_face - seal_w, -r_body, seal_w, 2.0 * r_body, fill=SEAL_COLOR, stroke=None),
        _poly(outline, fill="none"),
    ]
    csys = flagnote_csys_children("24", shell_size)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="400" height="400">
<g id="{part_number}-drawing-contents-start">
{chr(10).join(parts)}
</g>
<g id="{part_number}-drawing-contents-end">
</g>
{_csys_overlay_svg(csys)}
</svg>'''


def connector_svg(part_number, shell_type, shell_size, finish=None):
    if shell_type == "24":
        return series_iii_24_connector_svg(part_number, shell_size, finish)
    if shell_type == "26":
        return series_iii_26_connector_svg(part_number, shell_size, finish)
    raise ValueError(f"Unsupported shell type '{shell_type}'")


def compile_part_attributes(part_configuration):
    pn_arrangement = part_configuration.get("insert_arrangement")
    pn_arrangement_prefix = pn_arrangement[0]
    pn_arrangement_suffix = pn_arrangement[1:]

    if pn_arrangement_prefix == "A":
        shell_size = "9"
    elif pn_arrangement_prefix == "B":
        shell_size = "11"
    elif pn_arrangement_prefix == "C":
        shell_size = "13"
    elif pn_arrangement_prefix == "D":
        shell_size = "15"
    elif pn_arrangement_prefix == "E":
        shell_size = "17"
    elif pn_arrangement_prefix == "F":
        shell_size = "19"
    elif pn_arrangement_prefix == "G":
        shell_size = "21"
    elif pn_arrangement_prefix == "H":
        shell_size = "23"
    elif pn_arrangement_prefix == "J":
        shell_size = "25"

    else:
        raise ValueError(f"Invalid insert arrangement prefix: {pn_arrangement_prefix}")

    insert_arrangement = f"{shell_size}-{pn_arrangement_suffix}"
    
    # FIND CONTACTS
    contacts = INSERT_ARRANGEMENTS.get(insert_arrangement)

    # FIND UNIQUE CONTACT SIZES
    seen_contact_sizes = []
    for contact in contacts:
        if contact.get("size") not in seen_contact_sizes:
            seen_contact_sizes.append(contact.get("size"))

    # FIND RELEVANT TOOLS
    tools = []
    for contact_size in seen_contact_sizes:
        tools.append(f"{CONTACT_SIZES.get(contact_size).get('crimp_tool')} crimp tool")
        tools.append(f"{CONTACT_SIZES.get(contact_size).get('extraction_tool')} extraction tool")

    attributes = {
        "tools": tools,
        "build_notes": [],
        "csys_children": flagnote_csys_children(
            part_configuration.get("shell_type"),
            part_configuration.get("insert_arrangement")[0],
        ),
        "contacts": contacts,
        "shell_size": part_configuration.get("insert_arrangement")[0],
    }
    return attributes


def _progress_bar(done, total, width=25):
    """Return a text progress bar like: [ x x x . . . ] (35%)."""
    if total <= 0:
        filled = width
        pct = 100
    else:
        filled = min(width, max(0, round(width * done / total)))
        pct = round(100.0 * done / total)
    cells = ["x"] * filled + ["."] * (width - filled)
    return "[ " + " ".join(cells) + f" ] ({pct}%)"


def write_revision_history_if_missing(part_dir, part_number):
    revision_history_csv_path = os.path.join(
        part_dir, f"{part_number}-revision_history.tsv"
    )
    if os.path.exists(revision_history_csv_path):
        return
    rev_history.part_family_append(
        {
            "product": state.product,
            "mfg": "mil spec",
            "pn": part_number,
            "rev": REVISION,
            "desc": "",
            "status": "",
            "datestarted": DATE_STARTED,
            "library_repo": "https://github.com/harnice/harnice-aerospace-connector-library",
            "library_subpath": "D38999",
        },
        revision_history_csv_path,
    )


def cache_run_constant_lookups():
    """Resolve the per-part lookups that cannot change during a run, once.

    `rev_history.part_family_append` calls `get_git_hash_of_harnice_src` (which
    shells out to `git rev-parse`) and re-reads `drawnby.json` for every part.
    Neither value can change while the run is in flight.
    """
    git_hash = fileio.get_git_hash_of_harnice_src()
    drawnby = fileio.drawnby()
    fileio.get_git_hash_of_harnice_src = lambda: git_hash
    fileio.drawnby = lambda: drawnby


def build_part(part_number, rev_dir):
    """Run the harnice part build in this process.

    Equivalent to `harnice -b` in **rev_dir**, minus the checks the CLI performs
    that this generator has already satisfied: it wrote the revision history
    itself, so it does not need `verify_revision_structure` to discover the part
    number, re-derive the library identity, or refresh datemodified. Skipping
    the CLI avoids paying interpreter startup and a harnice import per part.
    """
    cwd = os.getcwd()
    os.chdir(rev_dir)
    try:
        state.set_pn(part_number)
        state.set_rev(REVISION)
        state.set_file_structure(part.file_structure())
        part.generate_structure()
        part.build()
    finally:
        os.chdir(cwd)


def main(step_only=False, svg_only=False, shell_types=None, use_cli=False):
    state.set_rev(REVISION)
    state.set_product("part")

    if not (step_only or svg_only):
        cache_run_constant_lookups()

    if shell_types is None:
        shell_types = ["24", "26"]

    part_configurations = []
    for shell_type in shell_types:
        for finish in ["F", "K", "W", "Z"]:
            for insert_arrangement in INSERT_ARRANGEMENT_CODES:
                for contact_type in ["P", "S"]:
                    for key in ["N", "A", "B", "C"]:
                        part_configurations.append(
                            {
                                "shell_type": shell_type,
                                "finish": finish,
                                "insert_arrangement": insert_arrangement,
                                "contact_type": contact_type,
                                "key": key,
                            }
                        )

    total = len(part_configurations)
    for i, part_configuration in enumerate(part_configurations, start=1):
        # GENERATE THE PART NUMBER
        part_number = f"D38999_{part_configuration['shell_type']}{part_configuration['finish']}{part_configuration['insert_arrangement']}{part_configuration['contact_type']}{part_configuration['key']}"
        print("Preparing part number: ", part_number)

        # MAKE THE PART FOLDER
        family_dir = os.path.dirname(os.path.abspath(__file__))
        part_dir = os.path.join(family_dir, part_number)
        os.makedirs(part_dir, exist_ok=True)

        rev_dir = os.path.join(part_dir, f"{part_number}-rev{REVISION}")
        if step_only or svg_only:
            os.makedirs(rev_dir, exist_ok=True)
            write_revision_history_if_missing(part_dir, part_number)
            attributes = compile_part_attributes(part_configuration)
            json_path = os.path.join(
                rev_dir, f"{part_number}-rev{REVISION}-attributes.json"
            )
            with open(json_path, "w") as f:
                json.dump(attributes, f, indent=2)
            if svg_only:
                svg_content = connector_svg(
                    part_number,
                    part_configuration.get("shell_type"),
                    attributes.get("shell_size"),
                    part_configuration.get("finish"),
                )
                svg_path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-drawing.svg")
                with open(svg_path, "w") as f:
                    f.write(svg_content)
            if step_only:
                write_part_step(
                    rev_dir,
                    part_number,
                    part_configuration.get("shell_type"),
                    attributes.get("shell_size"),
                )
            print(_progress_bar(i, total))
            continue

        # UPDATE THE REVISION HISTORY FILE
        revision_history_content_dict = {
            "product": state.product,
            "mfg": "mil spec",
            "pn": part_number,
            "rev": REVISION,
            "desc": "",
            "status": "",
            "datestarted": DATE_STARTED,
            "library_repo": "https://github.com/harnice/harnice-aerospace-connector-library",
            "library_subpath": "D38999"
        }
        revision_history_csv_path = os.path.join(
            part_dir, f"{part_number}-revision_history.tsv"
        )
        rev_history.part_family_append(
            revision_history_content_dict, revision_history_csv_path
        )

        # CLEAN AND MAKE THE REVISION FOLDER
        if os.path.exists(rev_dir):
            for item in os.listdir(rev_dir):
                item_path = os.path.join(rev_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
        else:
            os.makedirs(rev_dir)

        # WRITE THE ATTRIBUTES JSON
        json_path = os.path.join(
            rev_dir, f"{part_number}-rev{REVISION}-attributes.json"
        )
        attributes = compile_part_attributes(part_configuration)
        with open(json_path, "w") as f:
            json.dump(attributes, f, indent=2)


        # GENERATE THE SVG
        svg_content = connector_svg(
            part_number,
            part_configuration.get("shell_type"),
            attributes.get("shell_size"),
            part_configuration.get("finish"),
        )
        svg_path = os.path.join(rev_dir, f"{part_number}-rev{REVISION}-drawing.svg")
        with open(svg_path, "w") as f:
            f.write(svg_content)

        write_part_step(
            rev_dir,
            part_number,
            part_configuration.get("shell_type"),
            attributes.get("shell_size"),
        )

        # RENDER THE PART
        if use_cli:
            subprocess.run(['harnice', '-b'], cwd=rev_dir, check=True)
        else:
            build_part(part_number, rev_dir)
        if delete_pngs:
            for item in os.listdir(rev_dir):
                if item.endswith(".png"):
                    os.remove(os.path.join(rev_dir, item))

        print(_progress_bar(i, total))

    print("Finished rendering all parts in family.")

if __name__ == "__main__":
    shell_types = ["24", "26"]
    if "--24-only" in sys.argv:
        shell_types = ["24"]
    elif "--26-only" in sys.argv:
        shell_types = ["26"]
    main(
        step_only="--step-only" in sys.argv,
        svg_only="--svg-only" in sys.argv,
        shell_types=shell_types,
        use_cli="--cli" in sys.argv,
    )
