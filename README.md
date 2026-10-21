# NIDA_ATT

The NIDA shell and its system books, for Foolbook. This is a content pack, not the reader. Foolbook opens the books. Foolcourse can point a curriculum at this folder.

Built from the TBKX exports on 21 October 2026. The page lists match the binaries. The scripts are the export. NIDA writes `to get`, so Foolbook 1.0.5r6 or later is required.

| File | What it is |
|---|---|
| `nida81.fbk` | The shell. 44 pages. |
| `nc81base.fsk` | Basic functions, including `initializeBase`. |
| `nc81recs.fsk` | Session and student functions, including `openSession`. |
| `nc81test.fsk` | Quiz functions, including `initializeTest`. |
| `nc81trnr.fsk` | Trainer functions, including `initializeTrnr`. |
| `nc81bank.fsk` | Question-bank functions, including `initializeBank`. |

`bitmaps/` holds 43 pictures from those exports, as PPM. 38 belong to `nida81`, including `PaintObject4`. The other five, `Bitmap100` through `Bitmap104`, are shared by the system books. On the bank, 100 and 104 are swapped.

The original `.tbk`, `.sbk`, and `.dll` files are not here. The script text is NIDA's, from their books. This repository is not affiliated with NIDA, Asymetrix, Click2learn, or SumTotal.

Open the shell from a Foolbook checkout:

```bash
python3 -m foolbook /path/to/NIDA_ATT/nida81.fbk
```

Leave the `.fsk` files and `bitmaps/` beside that book.
