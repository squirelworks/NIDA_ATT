package main

import (
	"archive/zip"
	"os"
	"path/filepath"
	"testing"
)

func TestChoosePicksBooksAndTheMatchingProgram(t *testing.T) {
	assets := []asset{
		{Name: "NIDA_ATT-1.0.0-content.zip", URL: "https://example/content"},
		{Name: "NIDA_ATT-1.0.0-windows-x64.zip", URL: "https://example/windows"},
		{Name: "NIDA_ATT-1.0.0-linux-x64.zip", URL: "https://example/linux"},
		{Name: "NIDA_ATT-1.0.0-setup.exe", URL: "https://example/setup"},
	}
	books, program, err := choose(assets, "windows-x64")
	if err != nil {
		t.Fatal(err)
	}
	if books.Name != "NIDA_ATT-1.0.0-content.zip" || program.Name != "NIDA_ATT-1.0.0-windows-x64.zip" {
		t.Fatalf("got %s and %s", books.Name, program.Name)
	}
}

func TestInstallMergesTheProgramAndTheBooks(t *testing.T) {
	dir := t.TempDir()
	program := filepath.Join(dir, "program.zip")
	books := filepath.Join(dir, "books.zip")
	writeZip(t, program, map[string]string{
		"NIDA_ATT-1.0.0-windows-x64/python/python.exe": "py",
		"NIDA_ATT-1.0.0-windows-x64/NIDA_ATT.exe":      "exe",
	})
	writeZip(t, books, map[string]string{
		"NIDA_ATT-1.0.0-content/nida81.fbk":           "shell",
		"NIDA_ATT-1.0.0-content/courses/93950101.fbk": "book",
	})
	dest := filepath.Join(dir, "NIDA_ATT")
	if err := install(program, books, dest); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dest, "NIDA_ATT.exe")); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dest, "nida81.fbk")); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dest, "courses", "93950101.fbk")); err != nil {
		t.Fatal(err)
	}
}

func writeZip(t *testing.T, path string, files map[string]string) {
	t.Helper()
	file, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	zw := zip.NewWriter(file)
	for name, body := range files {
		w, err := zw.Create(name)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := w.Write([]byte(body)); err != nil {
			t.Fatal(err)
		}
	}
	if err := zw.Close(); err != nil {
		t.Fatal(err)
	}
}
