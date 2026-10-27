//go:build windows

package main

import (
	"os"
	"path/filepath"
	"syscall"
	"unsafe"
)

func fail(dir, msg string) {
	if dir == "" {
		if exe, err := os.Executable(); err == nil {
			dir = filepath.Dir(exe)
		}
	}
	if dir != "" {
		if f, err := os.OpenFile(filepath.Join(dir, "NIDA_ATT.log"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644); err == nil {
			_, _ = f.WriteString(msg + "\r\n")
			_ = f.Close()
		}
	}
	user32 := syscall.NewLazyDLL("user32.dll")
	box := user32.NewProc("MessageBoxW")
	text, _ := syscall.UTF16PtrFromString(msg)
	title, _ := syscall.UTF16PtrFromString("NIDA_ATT")
	box.Call(0, uintptr(unsafe.Pointer(text)), uintptr(unsafe.Pointer(title)), 0x10)
}
