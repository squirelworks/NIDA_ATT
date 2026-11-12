"""The DLL stand-ins answer with no hardware and no original DLL."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dlls.nc81int import FUNCTIONS as INT  # noqa: E402
from dlls.nc81rec import FUNCTIONS as REC  # noqa: E402


def state():
    return SimpleNamespace(variables={})


class Records(unittest.TestCase):
    def test_a_new_student_starts_and_a_later_check_restarts(self):
        host = state()
        self.assertEqual(REC["reccheckstatus"](host, ["S1", "93951303"], []), 0)
        index = REC["recstartsession"](host, ["S1", "93951303"], [])
        self.assertGreater(index, 0)
        self.assertEqual(REC["reccheckstatus"](host, ["S1", "93951303"], []), 1)
        self.assertEqual(REC["recrestartsession"](host, ["S1", "93951303"], []), index)

    def test_a_score_is_the_record_the_checks_read(self):
        host = state()
        index = REC["recstartsession"](host, ["S1", "lesson"], [])
        REC["recwriteresponse"](host, [index, 1, 2, 3, 0, "A", 100], [])
        self.assertEqual(host.variables["__responses"], [{
            "student": index, "type": 1, "test": 2, "question": 3,
            "part": 0, "response": "A", "score": 100,
        }])

    def test_a_bookmark_round_trips_and_a_close_starts_again(self):
        host = state()
        index = REC["recstartsession"](host, ["S1", "lesson"], [])
        REC["recwritevariable"](host, [index, "lastPage", "$P100"], [])
        host.variables["buf"] = ""
        REC["recreadvariable"](host, [index, "lastPage", 0], ["", "", "buf"])
        self.assertEqual(host.variables["buf"], "$P100")
        REC["recclosesession"](host, [index], [])
        self.assertEqual(REC["reccheckstatus"](host, ["S1", "lesson"], []), 0)


class Trainer(unittest.TestCase):
    def test_no_trainer_is_not_the_success_code(self):
        host = state()
        for name in ("intcheckcomm130e", "intstartcai130e", "intsendfaulttd2000", "intsetpower205e"):
            self.assertEqual(INT.get(name)(host, [1, 0], []), 0)
            self.assertNotEqual(INT.get(name)(host, [1, 0], []), 61)


if __name__ == "__main__":
    unittest.main()
