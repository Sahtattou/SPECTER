package providers

import "github.com/Sahtattou/SPECTER/pkg/models"

type Provider interface {
	Name() string
	Fetch(target string) (*models.ThreatRecord, error)
	Supports(targetType string) bool // NEW!
}
