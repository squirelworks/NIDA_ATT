// NIDA_ATT setup downloads the books and the program for this machine
// from the latest GitHub release, then puts them in one folder.
package main

import (
	"archive/zip"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

const repo = "squirelworks/NIDA_ATT"

func main() {
	dest := defaultDest()
	if len(os.Args) > 1 {
		dest = os.Args[1]
	}
	key := systemKey()
	if key == "" {
		fmt.Fprintf(os.Stderr, "This installer does not know %s/%s.\n", runtime.GOOS, runtime.GOARCH)
		os.Exit(1)
	}
	fmt.Println("NIDA_ATT setup")
	fmt.Printf("Downloading the books and the %s program.\n", key)
	fmt.Println("Installing into", dest)
	assets, err := latestAssets()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	books, program, err := choose(assets, key)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	tmp, err := os.MkdirTemp("", "nida-setup")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer os.RemoveAll(tmp)
	booksZip := filepath.Join(tmp, "books.zip")
	programZip := filepath.Join(tmp, "program.zip")
	if err := download(books.URL, booksZip, "books"); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := download(program.URL, programZip, "program"); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := install(programZip, booksZip, dest); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println()
	fmt.Println("Done.")
	fmt.Println("Open", startPath(dest, key))
}

func systemKey() string {
	switch runtime.GOOS + "/" + runtime.GOARCH {
	case "windows/amd64":
		return "windows-x64"
	case "linux/amd64":
		return "linux-x64"
	case "linux/arm64":
		return "linux-arm64"
	case "darwin/arm64":
		return "macos-arm64"
	case "darwin/amd64":
		return "macos-x64"
	default:
		return ""
	}
}

func defaultDest() string {
	exe, err := os.Executable()
	if err != nil {
		return "NIDA_ATT"
	}
	if resolved, err := filepath.EvalSymlinks(exe); err == nil {
		exe = resolved
	}
	return filepath.Join(filepath.Dir(exe), "NIDA_ATT")
}

func startPath(dest, key string) string {
	if strings.HasPrefix(key, "windows") {
		return filepath.Join(dest, "NIDA_ATT.exe")
	}
	if strings.HasPrefix(key, "macos") {
		return filepath.Join(dest, "NIDA_ATT.app")
	}
	return filepath.Join(dest, "NIDA_ATT")
}

type asset struct {
	Name string `json:"name"`
	URL  string `json:"browser_download_url"`
}

func latestAssets() ([]asset, error) {
	req, err := http.NewRequest(http.MethodGet, "https://api.github.com/repos/"+repo+"/releases/latest", nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "NIDA_ATT-setup")
	req.Header.Set("Accept", "application/vnd.github+json")
	token := os.Getenv("GH_TOKEN")
	if token == "" {
		token = os.Getenv("GITHUB_TOKEN")
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("GitHub returned %s for the latest release", resp.Status)
	}
	var body struct {
		Assets []asset `json:"assets"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		return nil, err
	}
	return body.Assets, nil
}

func choose(assets []asset, key string) (asset, asset, error) {
	var books, program asset
	for _, item := range assets {
		name := strings.ToLower(item.Name)
		if !strings.HasSuffix(name, ".zip") {
			continue
		}
		if strings.Contains(name, "content") {
			books = item
			continue
		}
		if strings.Contains(name, "setup") {
			continue
		}
		if strings.Contains(name, key) {
			program = item
		}
	}
	if books.URL == "" || program.URL == "" {
		return books, program, fmt.Errorf("the release is missing the books or the %s program", key)
	}
	return books, program, nil
}

func download(url, dest, label string) error {
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("User-Agent", "NIDA_ATT-setup")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("download %s returned %s", label, resp.Status)
	}
	file, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer file.Close()
	buf := make([]byte, 1<<20)
	var written int64
	for {
		n, readErr := resp.Body.Read(buf)
		if n > 0 {
			if _, err := file.Write(buf[:n]); err != nil {
				return err
			}
			written += int64(n)
			if resp.ContentLength > 0 {
				fmt.Printf("\r%s  %d / %d MB", label, written>>20, resp.ContentLength>>20)
			} else {
				fmt.Printf("\r%s  %d MB", label, written>>20)
			}
		}
		if readErr == io.EOF {
			fmt.Println()
			return nil
		}
		if readErr != nil {
			return readErr
		}
	}
}

func install(programZip, booksZip, dest string) error {
	tmp, err := os.MkdirTemp("", "nida-unpack")
	if err != nil {
		return err
	}
	defer os.RemoveAll(tmp)
	programDir := filepath.Join(tmp, "program")
	booksDir := filepath.Join(tmp, "books")
	if err := unzip(programZip, programDir); err != nil {
		return err
	}
	if err := unzip(booksZip, booksDir); err != nil {
		return err
	}
	programDir = singleRoot(programDir)
	booksDir = singleRoot(booksDir)
	if !hasShell(booksDir) {
		return fmt.Errorf("the books download has no nida81.fbk")
	}
	if err := os.RemoveAll(dest); err != nil {
		return err
	}
	if err := copyTree(programDir, dest); err != nil {
		return err
	}
	return copyTree(booksDir, dest)
}

func singleRoot(dir string) string {
	entries, err := os.ReadDir(dir)
	if err != nil || len(entries) != 1 || !entries[0].IsDir() {
		return dir
	}
	return filepath.Join(dir, entries[0].Name())
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

func unzip(src, dest string) error {
	reader, err := zip.OpenReader(src)
	if err != nil {
		return err
	}
	defer reader.Close()
	root := filepath.Clean(dest) + string(os.PathSeparator)
	if err := os.MkdirAll(dest, 0o755); err != nil {
		return err
	}
	for _, file := range reader.File {
		name := filepath.Clean(file.Name)
		if name == "." || strings.HasPrefix(name, "..") {
			return fmt.Errorf("bad path in zip: %s", file.Name)
		}
		target := filepath.Join(dest, name)
		if !strings.HasPrefix(target, root) && target != filepath.Clean(dest) {
			return fmt.Errorf("bad path in zip: %s", file.Name)
		}
		if file.FileInfo().IsDir() {
			if err := os.MkdirAll(target, 0o755); err != nil {
				return err
			}
			continue
		}
		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			return err
		}
		in, err := file.Open()
		if err != nil {
			return err
		}
		out, err := os.OpenFile(target, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, file.Mode())
		if err != nil {
			in.Close()
			return err
		}
		_, copyErr := io.Copy(out, in)
		in.Close()
		closeErr := out.Close()
		if copyErr != nil {
			return copyErr
		}
		if closeErr != nil {
			return closeErr
		}
	}
	return nil
}

func copyTree(src, dest string) error {
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		target := filepath.Join(dest, rel)
		if info.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			return err
		}
		in, err := os.Open(path)
		if err != nil {
			return err
		}
		defer in.Close()
		out, err := os.OpenFile(target, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, info.Mode())
		if err != nil {
			return err
		}
		_, copyErr := io.Copy(out, in)
		closeErr := out.Close()
		if copyErr != nil {
			return copyErr
		}
		return closeErr
	})
}
