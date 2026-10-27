"""Build the NIDA_ATT download for one system.

The zip is the whole course. Foolcourse is inside it, already pointed at
these books. A person downloads the zip for their machine, unzips it, and
starts NIDA_ATT.

    python3 pack/build.py linux-x64
    python3 pack/build.py windows-x64

`content` is only the books, for a Foolcourse that is already installed.
It is not the download a new person gets.
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
SETUPS = ROOT / "pack" / "setups"
SETUP_SRC = ROOT / "pack" / "setup"
VERSION = "1.0.0"
REPO = "squirelworks/NIDA_ATT"

SYSTEMS = ("windows-x64", "linux-x64", "linux-arm64", "macos-arm64", "macos-x64")

# What the Foolcourse pack copies in. Same commits Foolcourse and Foolbook pin.
CHECKOUTS = {
    "Foolbook": (
        "https://github.com/squirelworks/Foolbook.git",
        "bd701f434545a77ab3af20e6e0f1e860973f2558",
    ),
    "openscript_analysis": (
        "https://github.com/squirelworks/openscript_analysis.git",
        "d741054cf2536bbf9d031bf183f6aedd949ebb8c",
    ),
}

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


def ensure_checkouts(foolcourse: Path) -> None:
    """The Foolcourse pack copies these from the folder next to itself.

    An existing checkout is left alone. A missing one is cloned at the pin.
    """
    parent = foolcourse.parent
    for name, (url, pin) in CHECKOUTS.items():
        dest = parent / name
        if dest.is_dir() and (dest / "pyproject.toml").is_file():
            continue
        if dest.exists():
            raise SystemExit(f"{dest} is in the way and is not a checkout")
        print(f"cloning {name}", flush=True)
        subprocess.check_call(["git", "clone", url, str(dest)])
        subprocess.check_call(["git", "-C", str(dest), "checkout", "--detach", pin])


def build_program(foolcourse: Path, key: str) -> Path:
    ensure_checkouts(foolcourse)
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


def ensure_setup(key: str) -> Path:
    """The small program that downloads a system build and the books."""
    name = "NIDA_ATT-setup.exe" if key.startswith("windows") else "NIDA_ATT-setup"
    dest = SETUPS / key / name
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
    subprocess.check_call(
        [go, "build", "-ldflags", "-s -w", "-o", str(dest), "."],
        cwd=SETUP_SRC,
        env=env,
    )
    return dest


def build_setups() -> list[Path]:
    DIST.mkdir(parents=True, exist_ok=True)
    written = []
    for key in SYSTEMS:
        binary = ensure_setup(key)
        if key.startswith("windows"):
            name = f"NIDA_ATT-{VERSION}-setup.exe"
        else:
            name = f"NIDA_ATT-{VERSION}-setup-{key}"
        dest = DIST / name
        shutil.copy2(binary, dest)
        if not key.startswith("windows"):
            _mark_executable(dest)
        print(f"wrote {dest}", flush=True)
        written.append(dest)
    return written


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
        "This is the NIDA_ATT program. The books are not in this zip.\n\n"
        "On Windows, run NIDA_ATT-1.0.0-setup.exe from the same release.\n"
        "It downloads this program and the books, then puts them in one folder.\n\n"
        "To put them together yourself, unzip the content zip into this folder.\n"
        "nida81.fbk stays one level above courses.\n\n"
    )
    if key.startswith("windows"):
        body += "The program starts with NIDA_ATT.exe.\n"
    elif key.startswith("macos"):
        body += "The program starts with NIDA_ATT.app.\n"
    else:
        body += "The program starts with NIDA_ATT.\n"
    return body


CONTENT_START = """This zip is the books, the shell, and the curriculum. There is no program in it.

NIDA_ATT-1.0.0-setup.exe downloads this file. If you already have the program,
unzip this into that folder. nida81.fbk stays one level above courses.
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
    """The program for one system. The books stay in the content zip."""
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


def release_folder(key: str) -> Path:
    return DIST / f"NIDA_ATT-{VERSION}-{key}"


def content_archive() -> Path:
    return DIST / f"NIDA_ATT-{VERSION}-content.zip"


def zip_named(folder: Path, archive: Path) -> Path:
    if archive.exists():
        archive.unlink()
    print("zipping", flush=True)
    shutil.make_archive(str(archive.with_suffix("")), "zip", folder.parent, folder.name)
    print(f"wrote {archive} ({archive.stat().st_size} bytes)", flush=True)
    return archive


def publish() -> None:
    """Upload the zips in dist to the v1.0.0 GitHub release."""
    files = []
    content = content_archive()
    if content.is_file():
        files.append(content)
    for key in SYSTEMS:
        archive = release_folder(key).with_suffix(".zip")
        if archive.is_file():
            files.append(archive)
    files.extend(path for path in sorted(DIST.glob(f"NIDA_ATT-{VERSION}-setup*")) if path.is_file())
    if not files:
        raise SystemExit(f"nothing in {DIST} to publish")
    notes = """The books, the program for each system, and the Windows setup.

Run NIDA_ATT-1.0.0-setup.exe. It downloads the books and the Windows program from this release and puts them in one folder next to the setup program. Open NIDA_ATT.exe in that folder.

NIDA_ATT-1.0.0-content.zip is the books by themselves.
The other zips are the program for one system. They do not contain the books.
"""
    tag = f"v{VERSION}"
    view = subprocess.run(
        ["gh", "release", "view", tag, "--repo", REPO],
        capture_output=True,
        text=True,
    )
    if view.returncode != 0:
        subprocess.check_call(
            ["gh", "release", "create", tag, "--repo", REPO, "--title", f"NIDA_ATT {VERSION}", "--notes", notes]
        )
    subprocess.check_call(
        ["gh", "release", "upload", tag, "--repo", REPO, "--clobber", *[str(path) for path in files]]
    )
    print(f"published {tag}", flush=True)


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
    known = set(SYSTEMS) | {"all", "content", "setup", "publish"}
    if not args and program is None:
        raise SystemExit(
            "name what to build: content, setup, publish, "
            + ", ".join(SYSTEMS)
        )
    if program is None:
        unknown = [item for item in args if item not in known]
        if unknown:
            raise SystemExit(f"unknown: {', '.join(unknown)}. known: {', '.join(sorted(known))}")
    want_content = False
    want_setup = False
    want_publish = False
    if program is not None:
        _version, key = split_program_name(program)
        keys = [(key, program)]
        if args and args != [key]:
            raise SystemExit(f"--from is a {key} folder")
    else:
        want_publish = "publish" in args
        want_setup = "setup" in args or args == ["all"]
        want_content = "content" in args or args == ["all"]
        wanted = list(SYSTEMS) if args == ["all"] else [item for item in args if item in SYSTEMS]
        keys = []
        if wanted:
            foolcourse = find_foolcourse()
            if not zipping:
                for key in wanted:
                    keys.append((key, build_program(foolcourse, key)))
            else:
                keys = [(key, None) for key in wanted]
    if want_content:
        folder = DIST / f"NIDA_ATT-{VERSION}-content"
        if not zipping or not folder.is_dir():
            print(f"filling {folder.name}", flush=True)
            assemble_content(folder, ROOT)
        zip_named(folder, content_archive())
    for key, source in keys:
        folder = release_folder(key)
        if zipping and source is None:
            if not folder.is_dir():
                raise SystemExit(f"no folder to zip: {folder}")
            zip_release(folder)
            continue
        print(f"filling {folder.name}", flush=True)
        assemble(source, folder, key)
        zip_release(folder)
    if want_setup:
        build_setups()
    if want_publish:
        publish()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
