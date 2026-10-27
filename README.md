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
| `_curriculum/nida.curriculum.json` | The master list. 717 lessons: the nine programs, the rating-only lessons, and the 104 books neither menu named. |
| `_curriculum/master.xml` | The whole disk on the seven ATT subjects. Extra units are inserted as Mod 02.5, Mod 03.5, and so on, so the modules still run in order. |
| `_curriculum/programs/` | The nine programs in `nida.programs.xml`, with `nida.curriculum.json`. 527 lessons. There is no menu per program. |
| `_curriculum/ratings/` | One menu per rating. The rating name is not a column. Subjects, then modules, then courses. |
| `_curriculum/index.json` | The file names and the counts. |
| `_curriculum/titles.json` | Every lesson id, the title the master uses, and the other wording when the two menus disagree. |
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

The whole disk, programs and ratings and the 104 books neither menu named:

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

The lessons on the curriculum you named count toward the overall. A rating menu starts at the subjects, because you already chose the rating. A lesson that is on more than one program counts once. On the whole-disk menu, a subject is listed once. A Foolcourse release is still the empty program.
