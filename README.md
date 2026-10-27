# NIDA_ATT

The NIDA course. Foolcourse is the program and stays general. This folder is what that program is pointed at: the curriculum, the shell, and the books.

Not affiliated with NIDA, Asymetrix, Click2learn, or SumTotal.

## Layout

| Path | What it is |
|---|---|
| `nida81.fbk` | The shell. A lesson finds it one directory up. |
| `nc81base.fsk` | Basic functions, including `initializeBase`. |
| `nc81recs.fsk` | Session and student functions, including `openSession`. |
| `nc81test.fsk` | Quiz functions, including `initializeTest`. |
| `nc81trnr.fsk` | Trainer functions, including `initializeTrnr`. |
| `nc81bank.fsk` | Question-bank functions, including `initializeBank`. The export may name this `NC81BANK.fsk`. |
| `_curriculum/nida.curriculum.json` | The official list. 527 lessons. Anything else in `courses/` is extra. |
| `_curriculum/nida.programs.xml` | The menu. Titles and the grouping into programs. |
| `courses/` | The lesson `.fbk` files, flat. `__PUT_COURSES_HERE__` marks the folder. |

The original `.tbk`, `.sbk`, and `.dll` files are not part of the course.

## Put the books in

From a checkout that already has `original/` beside this README, the export Foolbook just wrote:

```bash
cd ~/FU/NIDA_ATT
mkdir -p courses
find original -iname '*.fbk' ! -iname 'nida81.fbk' -exec cp -n {} courses/ \;
for name in nida81.fbk nc81bank.fsk nc81base.fsk nc81recs.fsk nc81test.fsk nc81trnr.fsk; do
  found=$(find original -maxdepth 2 -iname "$name" -print -quit)
  if [ -n "$found" ]; then cp -f "$found" "$name"; fi
done
```

Do not leave `nida81.fbk` inside `courses/`. The loop keeps the shell and the five system books one directory up, whatever case the export used.

## Open it

Foolcourse from a source checkout does not load this list on its own. Point it here:

```bash
cd ~/FU/Foolcourse
.venv/bin/python -m foolcourse ~/FU/NIDA_ATT/courses \
  --curriculum ~/FU/NIDA_ATT/_curriculum/nida.curriculum.json
```

The menu is read because that curriculum is named `nida.`. A Foolcourse release is still the empty program. Dropping books into its own `courses/` is for some other deployment, not this one.
