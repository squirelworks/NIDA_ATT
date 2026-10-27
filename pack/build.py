"""Build the two NIDA_ATT downloads. Foolcourse stays the general program.

The books are one zip. The program that opens them is another, per system.

    python3 pack/build.py content
    python3 pack/build.py windows-x64
    python3 pack/build.py --from ~/FU/Foolcourse/dist/Foolcourse-1.0.1r2-windows-x64

Unzip both in the same place. The content folder is NIDA_ATT-content. The program
folder sits beside it. Windows starts with NIDA_ATT.exe, Linux with NIDA_ATT,
Mac with NIDA_ATT.app.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
LAUNCHERS = ROOT / "pack" / "launchers"
LAUNCHER_SRC = ROOT / "pack" / "launcher"

SYSTEMS = ("windows-x64", "linux-x64", "linux-arm64", "macos-arm64", "macos-x64")

SHELL = (
    "nida81.fbk",
    "nc81base.fsk",
    "nc81recs.fsk",
    "nc81test.fsk",
    "nc81trnr.fsk",
    "nc81bank.fsk",
)

SCRIPTS = (
    "Foolcourse.bat",
    "Foolcourse-console.bat",
    "Foolcourse.sh",
    "Foolcourse.command",
)

MAC_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>NIDA_ATT</string>
  <key>CFBundleIdentifier</key>
  <string>local.nida-att</string>
  <key>CFBundleName</key>
  <string>NIDA_ATT</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>LSMinimumSystemVersion</key>
  <string>11.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
"""


def find_foolcourse() -> Path:
    env = os.environ.get("FOOLCOURSE")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.extend(
        [
            ROOT.parent / "Foolcourse",
            Path.home() / "FU" / "Foolcourse",
            Path("/tmp/scope/Foolcourse"),
        ]
    )
    for path in candidates:
        if (path / "pack" / "build.py").is_file() and (path / "foolcourse").is_dir():
            return path.resolve()
    raise SystemExit("Foolcourse checkout not found. Set FOOLCOURSE to it.")


def foolcourse_version(foolcourse: Path) -> str:
    for line in (foolcourse / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{foolcourse} has no version")


def split_program_name(folder: Path) -> tuple[str, str]:
    """Foolcourse-1.0.1r2-windows-x64 -> ('1.0.1r2', 'windows-x64')."""
    name = folder.name
    for key in sorted(SYSTEMS, key=len, reverse=True):
        suffix = "-" + key
        if name.endswith(suffix):
            head = name[: -len(suffix)]
            version = head.split("-", 1)[1] if "-" in head else head
            return version, key
    raise SystemExit(
        f"{folder.name} is not a Foolcourse pack folder. "
        f"Expected a name ending in one of: {', '.join(SYSTEMS)}"
    )


def build_program(foolcourse: Path, key: str) -> Path:
    subprocess.check_call([sys.executable, str(foolcourse / "pack" / "build.py"), key], cwd=foolcourse)
    version = foolcourse_version(foolcourse)
    folder = foolcourse / "dist" / f"Foolcourse-{version}-{key}"
    if not folder.is_dir():
        raise SystemExit(f"Foolcourse build did not write {folder}")
    return folder


def _go() -> str | None:
    found = shutil.which("go")
    return found


def ensure_launcher(key: str) -> Path:
    name = "NIDA_ATT.exe" if key.startswith("windows") else "NIDA_ATT"
    dest = LAUNCHERS / key / name
    if dest.is_file():
        return dest
    go = _go()
    if not go:
        raise SystemExit(f"missing {dest}. Install Go and run this again so it can be built.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    goos, goarch = {
        "windows-x64": ("windows", "amd64"),
        "linux-x64": ("linux", "amd64"),
        "linux-arm64": ("linux", "arm64"),
        "macos-arm64": ("darwin", "arm64"),
        "macos-x64": ("darwin", "amd64"),
    }[key]
    env = os.environ.copy()
    env["CGO_ENABLED"] = "0"
    env["GOOS"] = goos
    env["GOARCH"] = goarch
    ldflags = "-s -w"
    if goos == "windows":
        ldflags = "-H windowsgui -s -w"
    subprocess.check_call(
        [go, "build", "-ldflags", ldflags, "-o", str(dest), "."],
        cwd=LAUNCHER_SRC,
        env=env,
    )
    return dest


def _mark_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _write(path: Path, text: str, *, crlf: bool = False) -> None:
    newline = "\r\n" if crlf else "\n"
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))


def install_curriculum(course: Path, dest: Path) -> None:
    src = course / "_curriculum"
    if not (src / "nida.curriculum.json").is_file() or not (src / "master.xml").is_file():
        raise SystemExit("the course has no master curriculum")
    out = dest / "_curriculum"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out)
    shutil.copy2(out / "master.xml", out / "nida.xml")
    for name in ("example.curriculum.json", "example.xml", "taxes.curriculum.json"):
        leftover = out / name
        if leftover.is_file():
            leftover.unlink()


def install_courses(course: Path, dest: Path) -> None:
    books = sorted(path for path in (course / "courses").glob("*.fbk") if path.is_file())
    if not books:
        raise SystemExit("courses/ has no .fbk files")
    out = dest / "courses"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    for book in books:
        shutil.copy2(book, out / book.name)


def install_shell(course: Path, dest: Path) -> None:
    found = {path.name.lower(): path for path in course.iterdir() if path.is_file()}
    missing = [name for name in SHELL if name.lower() not in found]
    if missing:
        raise SystemExit("missing shell file: " + ", ".join(missing))
    for name in SHELL:
        src = found[name.lower()]
        shutil.copy2(src, dest / src.name)


def install_launcher(key: str, dest: Path) -> None:
    binary = ensure_launcher(key)
    if key.startswith("windows"):
        shutil.copy2(binary, dest / "NIDA_ATT.exe")
        return
    target = dest / "NIDA_ATT"
    shutil.copy2(binary, target)
    _mark_executable(target)
    if key.startswith("macos"):
        macos = dest / "NIDA_ATT.app" / "Contents" / "MacOS"
        macos.mkdir(parents=True)
        bundled = macos / "NIDA_ATT"
        shutil.copy2(binary, bundled)
        _mark_executable(bundled)
        _write(dest / "NIDA_ATT.app" / "Contents" / "Info.plist", MAC_PLIST)


def start_text(key: str) -> str:
    body = (
        "This folder is Foolcourse, already set up for the NIDA course.\n"
        "The books are not in here. They are the other download.\n\n"
        "Unzip this whole folder. Do not run it from inside the zip.\n"
        "Unzip the content folder next to this one. It is named NIDA_ATT-content.\n\n"
    )
    if key.startswith("windows"):
        body += "Double-click NIDA_ATT.exe.\n"
    elif key.startswith("macos"):
        body += (
            "Double-click NIDA_ATT.app.\n"
            "If macOS says it cannot be opened, right-click NIDA_ATT.app, choose Open, "
            "then Open again. This copy is not signed with Apple.\n"
            "A terminal in this folder can run ./NIDA_ATT instead.\n"
        )
    else:
        body += "Double-click NIDA_ATT, or in a terminal run: ./NIDA_ATT\n"
    body += "\nIf the window does not open, read NIDA_ATT.log in this folder.\n"
    return body


CONTENT_START = """This folder is the NIDA course: the books, the shell, and the curriculum.

Unzip it next to the NIDA_ATT program folder, then start that program.
The program is the other download. This one has no Foolcourse in it.

The list the program opens is the master. nida81.fbk and the nc81 files stay
in this folder, one level above courses. A lesson looks for them there.

A Foolcourse you already built can use this folder too. Point it at courses
and at _curriculum/nida.curriculum.json with _curriculum/nida.xml.
"""


def assemble_content(dest: Path, course: Path) -> None:
    """The massive folder by itself. No Python and no Foolcourse."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    install_curriculum(course, dest)
    install_courses(course, dest)
    install_shell(course, dest)
    _write(dest / "START.txt", CONTENT_START)


def assemble(program: Path, dest: Path, key: str) -> None:
    """A Foolcourse folder that starts this course. The books stay next door."""
    if not program.is_dir():
        raise SystemExit(f"no Foolcourse folder: {program}")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(program, dest, symlinks=True)
    for name in ("_curriculum", "courses"):
        path = dest / name
        if path.exists():
            shutil.rmtree(path)
    for name in SCRIPTS:
        script = dest / name
        if script.is_file():
            script.unlink()
    install_launcher(key, dest)
    _write(dest / "START.txt", start_text(key), crlf=key.startswith("windows"))


def zip_release(folder: Path) -> Path:
    archive = folder.with_suffix(".zip")
    if archive.exists():
        archive.unlink()
    print("zipping", flush=True)
    shutil.make_archive(str(archive.with_suffix("")), "zip", folder.parent, folder.name)
    print(f"wrote {archive} ({archive.stat().st_size} bytes)", flush=True)
    return archive


def release_folder(version: str, key: str) -> Path:
    return DIST / f"NIDA_ATT-{version}-{key}"


def content_folder() -> Path:
    return DIST / "NIDA_ATT-content"


def zip_named(folder: Path, archive: Path) -> Path:
    if archive.exists():
        archive.unlink()
    print("zipping", flush=True)
    shutil.make_archive(str(archive.with_suffix("")), "zip", folder.parent, folder.name)
    print(f"wrote {archive} ({archive.stat().st_size} bytes)", flush=True)
    return archive


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    program = None
    if "--from" in args:
        index = args.index("--from")
        if index + 1 >= len(args):
            raise SystemExit("--from needs the Foolcourse pack folder")
        program = Path(args[index + 1]).expanduser().resolve()
        del args[index : index + 2]
    zipping = "--zip" in args
    args = [item for item in args if item != "--zip"]
    if not args and program is None:
        raise SystemExit(
            "name what to build: content, "
            + ", ".join(SYSTEMS)
            + "\n  or: python3 pack/build.py --from <Foolcourse-folder>"
        )
    want_content = False
    if program is not None:
        version, key = split_program_name(program)
        keys = [(key, version, program)]
        if args and args != [key]:
            raise SystemExit(f"--from is a {key} folder")
    else:
        unknown = [item for item in args if item not in SYSTEMS and item not in ("all", "content")]
        if unknown:
            raise SystemExit(f"unknown: {', '.join(unknown)}. known: content, {', '.join(SYSTEMS)}")
        want_content = "content" in args or args == ["all"]
        wanted = list(SYSTEMS) if args == ["all"] else [item for item in args if item in SYSTEMS]
        version = ""
        keys = []
        if wanted:
            foolcourse = find_foolcourse()
            version = foolcourse_version(foolcourse)
            if not zipping:
                for key in wanted:
                    keys.append((key, version, build_program(foolcourse, key)))
            else:
                keys = [(key, version, None) for key in wanted]
    if want_content:
        folder = content_folder()
        if not zipping or not folder.is_dir():
            print(f"filling {folder.name}", flush=True)
            assemble_content(folder, ROOT)
        zip_named(folder, DIST / "NIDA_ATT-content.zip")
    for key, version, source in keys:
        folder = release_folder(version, key)
        if zipping and source is None:
            if not folder.is_dir():
                raise SystemExit(f"no folder to zip: {folder}")
            zip_release(folder)
            continue
        print(f"filling {folder.name}", flush=True)
        assemble(source, folder, key)
        zip_release(folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
