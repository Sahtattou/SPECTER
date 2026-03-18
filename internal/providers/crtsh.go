package providers

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/go-resty/resty/v2"
)

type crtShEntry struct {
	NameValue string `json:"name_value"`
}

type CRTShProvider struct {
	client *resty.Client
}

func NewCRTShProvider() *CRTShProvider {
	return &CRTShProvider{
		client: resty.New().SetTimeout(45 * time.Second).SetRetryCount(2),
	}
}

func (p *CRTShProvider) Name() string { return "crt.sh" }

func (p *CRTShProvider) Collect(ctx context.Context) ([]models.Threat, error) {
	target := "%.example"
	if deadline, ok := ctx.Deadline(); ok {
		_ = deadline
	}

	var result []crtShEntry
	resp, err := p.client.R().
		SetContext(ctx).
		SetQueryParam("q", target).
		SetQueryParam("output", "json").
		SetResult(&result).
		Get("https://crt.sh/")
	if err != nil {
		return nil, fmt.Errorf("crt.sh request failed: %w", err)
	}
	if resp.IsError() {
		return nil, fmt.Errorf("crt.sh returned error: %s", resp.Status())
	}

	seen := make(map[string]struct{})
	threats := make([]models.Threat, 0, len(result))
	for _, entry := range result {
		names := strings.Split(entry.NameValue, "\n")
		for _, n := range names {
			domain := strings.TrimSpace(strings.TrimPrefix(n, "*."))
			if domain == "" {
				continue
			}
			if _, ok := seen[domain]; ok {
				continue
			}
			seen[domain] = struct{}{}
			threats = append(threats, models.Threat{
				IOCValue:    domain,
				IOCType:     "domain",
				SourceName:  p.Name(),
				SourceURL:   "https://crt.sh/",
				SourceQuery: target,
				RawEvidence: map[string]any{
					"name_value": entry.NameValue,
				},
				CollectedAt:   time.Now().UTC(),
				Corroboration: 1,
			})
		}
	}

	return threats, nil
}
