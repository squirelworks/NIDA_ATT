"""The content zip is the books. A system zip is the program without them."""

import importlib.util
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nida_pack", ROOT / "pack" / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def _course(path: Path) -> None:
    (path / "_curriculum").mkdir(parents=True)
    (path / "_curriculum" / "nida.curriculum.json").write_text("{}\n", encoding="utf-8")
    (path / "_curriculum" / "master.xml").write_text("<Document/>\n", encoding="utf-8")
    (path / "courses").mkdir()
    (path / "courses" / "93950101.fbk").write_bytes(b"fbk")
    (path / "courses" / "__PUT_COURSES_HERE__").write_text("no\n", encoding="utf-8")
    for name in build.SHELL:
        (path / name).write_bytes(b"shell")


def _program(path: Path) -> None:
    (path / "_curriculum").mkdir(parents=True)
    (path / "_curriculum" / "example.curriculum.json").write_text("{}\n", encoding="utf-8")
    (path / "courses").mkdir()
    (path / "courses" / "PUT COURSES HERE.txt").write_text("empty\n", encoding="utf-8")
    (path / "Foolcourse.bat").write_text("@echo off\n", encoding="utf-8")
    python = path / "python" / "bin"
    python.mkdir(parents=True)
    script = python / "python3"
    script.write_text(
        "#!/bin/sh\n"
        "{\n"
        '  echo "HOME=$FOOLCOURSE_HOME"\n'
        '  echo "PY=$PYTHONPATH"\n'
        '  echo "ARGS=$*"\n'
        '} > "$FOOLCOURSE_HOME/started.txt"\n',
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    (path / "app").mkdir()


class BuildTests(unittest.TestCase):
    def test_the_program_zip_does_not_carry_the_books(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            course = root / "course"
            program = root / "Foolcourse-1.0-linux-x64"
            _course(course)
            _program(program)
            content = root / "NIDA_ATT-1.0.0-content"
            play = root / "play"
            build.assemble_content(content, course)
            build.assemble(program, play, "linux-x64")
            self.assertTrue((content / "courses" / "93950101.fbk").is_file())
            self.assertFalse((content / "courses" / "__PUT_COURSES_HERE__").exists())
            self.assertTrue((content / "nida81.fbk").is_file())
            self.assertEqual((content / "_curriculum" / "nida.xml").read_text(encoding="utf-8"), "<Document/>\n")
            self.assertFalse((content / "NIDA_ATT").exists())
            self.assertFalse((play / "courses").exists())
            self.assertFalse((play / "nida81.fbk").exists())
            self.assertFalse((play / "_curriculum").exists())
            self.assertFalse((play / "Foolcourse.bat").exists())
            self.assertTrue((play / "NIDA_ATT").is_file())
            self.assertIn("books are not in this zip", (play / "START.txt").read_text(encoding="utf-8"))
            self.assertIn("no program in it", (content / "START.txt").read_text(encoding="utf-8"))

    def test_launcher_uses_the_content_folder_beside_it(self):
        launcher = ROOT / "pack" / "launchers" / "linux-x64" / "NIDA_ATT"
        if not launcher.is_file():
            self.skipTest("linux launcher is not built")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            course = root / "NIDA_ATT"
            program = root / "NIDA_ATT-1.0-linux-x64"
            _course(course)
            _program(program)
            binary = program / "NIDA_ATT"
            binary.write_bytes(launcher.read_bytes())
            binary.chmod(binary.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            subprocess.check_call([str(binary)], cwd=program)
            started = (course / "started.txt").read_text(encoding="utf-8")
            self.assertIn(f"HOME={course}", started)
            self.assertIn(f"PY={program / 'app'}", started)
            self.assertIn("ARGS=-m foolcourse", started)

    def test_an_existing_checkout_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            foolcourse = root / "Foolcourse"
            (foolcourse / "pack").mkdir(parents=True)
            for name in build.CHECKOUTS:
                dest = root / name
                dest.mkdir()
                (dest / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
                (dest / "marker").write_text("keep\n", encoding="utf-8")
            build.ensure_checkouts(foolcourse)
            for name in build.CHECKOUTS:
                self.assertEqual((root / name / "marker").read_text(encoding="utf-8"), "keep\n")


if __name__ == "__main__":
    unittest.main()
