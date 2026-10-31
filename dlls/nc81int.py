"""Stand-in for nc81int.dll. The original DLL is not part of this course.

nc81trnr treats 61 as a trainer that answered. Every call here returns 0,
so the lesson takes its no-trainer path. There is no port and no hardware.
"""

from __future__ import annotations


def _none(state, args, refs):
    return 0


class _NoTrainer(dict):
    def get(self, key, default=None):
        return _none


FUNCTIONS = _NoTrainer()
