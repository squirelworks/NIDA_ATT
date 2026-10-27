//go:build !windows

package main

import (
	"fmt"
	"os"
	"path/filepath"
)

func fail(dir, msg string) {
	if dir == "" {
		if exe, err := os.Executable(); err == nil {
			dir = filepath.Dir(exe)
		}
	}
	if dir != "" {
		if f, err := os.OpenFile(filepath.Join(dir, "NIDA_ATT.log"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644); err == nil {
			_, _ = f.WriteString(msg + "\n")
			_ = f.Close()
		}
	}
	fmt.Fprintln(os.Stderr, msg)
}
