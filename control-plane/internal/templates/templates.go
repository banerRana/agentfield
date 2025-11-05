package templates

import (
	"embed"
	"io/fs"
	"strings"
	"text/template"
)

//go:embed agent/*.tmpl agent/*/*.tmpl
var content embed.FS

// TemplateData holds the data to be passed to the templates.
type TemplateData struct {
	ProjectName string
	NodeID      string
	Port        int
	CreatedAt   string
	AuthorName  string
	AuthorEmail string
	CurrentYear int
}

// GetTemplate retrieves a specific template by its path.
func GetTemplate(name string) (*template.Template, error) {
	tmpl, err := template.ParseFS(content, name)
	if err != nil {
		return nil, err
	}
	return tmpl, nil
}

// GetTemplateFiles returns a map of template file paths relative to the embed.FS root.
func GetTemplateFiles() (map[string]string, error) {
	files := make(map[string]string)
	err := fs.WalkDir(content, ".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() {
			// Remove the "agent/" prefix and ".tmpl" suffix
			relativePath := strings.TrimPrefix(path, "agent/")
			relativePath = strings.TrimSuffix(relativePath, ".tmpl")
			files[path] = relativePath
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	return files, nil
}

// ReadTemplateContent reads the content of an embedded template file.
func ReadTemplateContent(path string) ([]byte, error) {
	return content.ReadFile(path)
}
