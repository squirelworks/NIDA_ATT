"""Stand-in for nc81rec.dll. The original DLL is not part of this course.

Sessions stay in the reader's variables for this run. RecCheckStatus
returns 1 when that student and lesson already have a session, which is
what nc81recs uses to restart instead of start. RecWriteResponse appends
the same record the quiz checks read from `__responses`.
"""

from __future__ import annotations


def _key(args):
    got = list(args) + ["", ""]
    return str(got[0]), str(got[1])


def _sessions(state):
    return state.variables.setdefault("__nc81sessions", {})


def _session(state, index):
    for row in _sessions(state).values():
        if row["index"] == index or str(row["index"]) == str(index):
            return row
    return None


def _open(state, student, lesson):
    sessions = _sessions(state)
    row = sessions.get((student, lesson))
    if row is not None and not row["closed"]:
        return row
    index = int(state.variables.get("__nc81next", 1) or 1)
    state.variables["__nc81next"] = index + 1
    row = {"index": index, "vars": {}, "closed": False}
    sessions[(student, lesson)] = row
    return row


def rec_check_status(state, args, refs):
    student, lesson = _key(args)
    row = _sessions(state).get((student, lesson))
    return 1 if row is not None and not row["closed"] else 0


def rec_start_session(state, args, refs):
    student, lesson = _key(args)
    return _open(state, student, lesson)["index"]


def rec_restart_session(state, args, refs):
    return rec_start_session(state, args, refs)


def rec_close_session(state, args, refs):
    row = _session(state, (list(args) + [0])[0])
    if row is not None:
        row["closed"] = True
    return 0


def rec_bookmark_session(state, args, refs):
    return 0


def rec_clear_variables(state, args, refs):
    row = _session(state, (list(args) + [0])[0])
    if row is not None:
        row["vars"].clear()
    return 0


def rec_write_variable(state, args, refs):
    got = list(args) + [0, "", ""]
    row = _session(state, got[0])
    if row is not None:
        row["vars"][str(got[1])] = "" if got[2] is None else str(got[2])
    return 0


def rec_read_variable(state, args, refs):
    got = list(args) + [0, "", None]
    row = _session(state, got[0])
    text = "" if row is None else row["vars"].get(str(got[1]), "")
    if len(refs) > 2 and refs[2]:
        state.variables[refs[2]] = text
    return 0


def rec_write_response(state, args, refs):
    got = list(args) + [0, 0, 0, 0, 0, "", 0]
    state.variables.setdefault("__responses", []).append({
        "student": got[0],
        "type": got[1],
        "test": got[2],
        "question": got[3],
        "part": got[4],
        "response": "" if got[5] is None else str(got[5]),
        "score": got[6],
    })
    return 0


FUNCTIONS = {
    "reccheckstatus": rec_check_status,
    "recstartsession": rec_start_session,
    "recrestartsession": rec_restart_session,
    "recclosesession": rec_close_session,
    "recbookmarksession": rec_bookmark_session,
    "recclearvariables": rec_clear_variables,
    "recwritevariable": rec_write_variable,
    "recreadvariable": rec_read_variable,
    "recwriteresponse": rec_write_response,
}
