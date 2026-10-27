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
| `_curriculum/nida.curriculum.json` | The master list. The 611 lessons that have a book in `courses/`. |
| `_curriculum/master.xml` | Those 611 books on the seven ATT subjects. Module numbers match the full map, including Mod 02.5 and the rest. |
| `_curriculum/programs/` | The nine programs in `nida.programs.xml`, with `nida.curriculum.json`. 527 lessons. There is no menu per program. |
| `_curriculum/ratings/` | One menu per rating. The rating name is not a column. Subjects, then modules, then courses. |
| `_curriculum/index.json` | The file names and the counts. |
| `_curriculum/titles.json` | The lesson ids on the master, the title the master uses, and the other wording when the two menus disagree. |
| `_inferred/` | The full placement of the 717 official lessons, including the 106 with no book in this repo. |
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

The nine programs, which is how that list arrived. Foolcourse finds `nida.programs.xml` beside a curriculum named `nida.`:

```bash
cd ~/FU/Foolcourse
.venv/bin/python -m foolcourse ~/FU/NIDA_ATT/courses \
  --curriculum ~/FU/NIDA_ATT/_curriculum/programs/nida.curriculum.json
```

The books in this repo. Placement comes from the full map, and a lesson is listed only when its `.fbk` is in `courses/`:

```bash
cd ~/FU/Foolcourse
.venv/bin/python -m foolcourse ~/FU/NIDA_ATT/courses \
  --curriculum ~/FU/NIDA_ATT/_curriculum/nida.curriculum.json \
  --xml ~/FU/NIDA_ATT/_curriculum/master.xml
```

One program, or one rating. `index.json` has the file names.

```bash
.venv/bin/python -m foolcourse ~/FU/NIDA_ATT/courses \
  --curriculum ~/FU/NIDA_ATT/_curriculum/ratings/em.curriculum.json \
  --xml ~/FU/NIDA_ATT/_curriculum/ratings/em.xml
```

The lessons on the curriculum you named count toward the overall. A rating menu starts at the subjects, because you already chose the rating. A lesson that is on more than one program counts once. On the master, a subject is listed once. Ratings and programs still name every lesson on those disks, including ones that are not in `courses/`. The full placement of all 717, present or not, is in `_inferred/`. A Foolcourse release is still the empty program.

## Download

Two downloads. The books are their own zip. The program that opens them is a smaller one, per system, and it sits beside the books.

Foolcourse stays the general program. The program zip is that program with nothing else to install. Windows starts with `NIDA_ATT.exe`. Linux starts with `NIDA_ATT`. Mac starts with `NIDA_ATT.app`. None of those is a script. The books are not inside that zip.

A Foolcourse checkout has to be next to this one, or `FOOLCOURSE` has to name it. The program build also needs Foolbook and openscript_analysis next to that checkout. If either is missing, this build clones it. Building a system downloads Python the first time. Later builds can reuse the folder.

```bash
cd ~/FU/NIDA_ATT
python3 pack/build.py content
python3 pack/build.py windows-x64
python3 pack/build.py --from ~/FU/Foolcourse/dist/Foolcourse-1.0.1r2-windows-x64
```

`dist/NIDA_ATT-content.zip` unpacks to a folder named `NIDA_ATT-content`: the books, the shell, and the curriculum. `dist/NIDA_ATT-<foolcourse version>-<system>.zip` is the program. Unzip both in the same place, then double-click the program. It uses the `NIDA_ATT-content` folder next to it as the course. `_curriculum/nida.curriculum.json` and `_curriculum/nida.xml` are the master. The shell stays one level above `courses/`.

