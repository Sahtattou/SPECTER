package providers

import (
	"context"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

type Provider interface {
	Name() string
	Collect(ctx context.Context) ([]models.Threat, error)
}
