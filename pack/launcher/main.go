// NIDA_ATT starts the bundled Foolcourse on the books in this same folder.
//
// A download for one system already contains the books. If it does not,
// the books may sit in a folder next to this program. This file is
// NIDA_ATT.exe on Windows, NIDA_ATT on Linux, and NIDA_ATT plus
// NIDA_ATT.app on Mac. A Mac app keeps the binary in Contents/MacOS, so
// the program folder is found by walking up to python/.
package main

import (
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

func main() {
	program, python, err := findProgram()
	if err != nil {
		fail(program, err.Error())
		os.Exit(1)
	}
	home, err := findContent(program)
	if err != nil {
		fail(program, err.Error())
		os.Exit(1)
	}
	cmd := exec.Command(python, "-m", "foolcourse")
	cmd.Dir = home
	cmd.Env = append(os.Environ(),
		"FOOLCOURSE_HOME="+home,
		"PYTHONPATH="+filepath.Join(program, "app"),
	)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fail(program, "Foolcourse did not start.\n\n"+err.Error())
		os.Exit(1)
	}
}

func findProgram() (string, string, error) {
	exe, err := os.Executable()
	if err != nil {
		return "", "", err
	}
	if resolved, err := filepath.EvalSymlinks(exe); err == nil {
		exe = resolved
	}
	dir := filepath.Dir(exe)
	for i := 0; i < 8; i++ {
		if python := pythonPath(dir); python != "" {
			return dir, python, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return filepath.Dir(exe), "", errors.New("cannot find the bundled Python next to NIDA_ATT")
}

func findContent(program string) (string, error) {
	if isContent(program) {
		return program, nil
	}
	parent := filepath.Dir(program)
	if isContent(parent) {
		return parent, nil
	}
	entries, err := os.ReadDir(parent)
	if err != nil {
		return "", missingContent()
	}
	var found []string
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		path := filepath.Join(parent, entry.Name())
		if path == program {
			continue
		}
		if isContent(path) {
			found = append(found, path)
		}
	}
	for _, path := range found {
		name := filepath.Base(path)
		if name == "NIDA_ATT" || name == "NIDA_ATT-content" {
			return path, nil
		}
	}
	if len(found) == 1 {
		return found[0], nil
	}
	return "", missingContent()
}

func missingContent() error {
	return errors.New("Put the NIDA_ATT content folder next to this program.\n\nThis download is Foolcourse. The books are the other download.")
}

func isContent(dir string) bool {
	return hasShell(dir) && hasBook(dir)
}

func hasShell(dir string) bool {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return false
	}
	for _, entry := range entries {
		if strings.EqualFold(entry.Name(), "nida81.fbk") {
			return true
		}
	}
	return false
}

func hasBook(dir string) bool {
	entries, err := os.ReadDir(filepath.Join(dir, "courses"))
	if err != nil {
		return false
	}
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if strings.HasSuffix(strings.ToLower(entry.Name()), ".fbk") {
			return true
		}
	}
	return false
}

func pythonPath(dir string) string {
	var rel string
	if runtime.GOOS == "windows" {
		rel = filepath.Join(dir, "python", "pythonw.exe")
	} else {
		rel = filepath.Join(dir, "python", "bin", "python3")
	}
	info, err := os.Stat(rel)
	if err != nil || info.IsDir() {
		return ""
	}
	return rel
}
