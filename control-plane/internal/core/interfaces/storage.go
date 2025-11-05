// brain/internal/core/interfaces/storage.go
package interfaces

import "github.com/your-org/brain/control-plane/internal/core/domain"

type FileSystemAdapter interface {
    ReadFile(path string) ([]byte, error)
    WriteFile(path string, data []byte) error
    Exists(path string) bool
    CreateDirectory(path string) error
    ListDirectory(path string) ([]string, error)
}

type RegistryStorage interface {
    LoadRegistry() (*domain.InstallationRegistry, error)
    SaveRegistry(registry *domain.InstallationRegistry) error
    GetPackage(name string) (*domain.InstalledPackage, error)
    SavePackage(name string, pkg *domain.InstalledPackage) error
}

type ConfigStorage interface {
    LoadBrainConfig(path string) (*domain.BrainConfig, error)
    SaveBrainConfig(path string, config *domain.BrainConfig) error
}
