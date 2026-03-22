package providers

import (
	"context"
	"fmt"
	"net"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/go-resty/resty/v2"
)

type otxResponse struct {
	PulseInfo struct {
		Count int `json:"count"`
	} `json:"pulse_info"`
}

type OTXProvider struct {
	apiKey  string
	client  *resty.Client
	targets []string
}

func NewOTXProvider(apiKey string, targets []string) *OTXProvider {
	return &OTXProvider{
		apiKey:  apiKey,
		client:  resty.New().SetTimeout(10 * time.Second),
		targets: targets,
	}
}

func (p *OTXProvider) Name() string { return "otx" }

func (p *OTXProvider) Collect(ctx context.Context) ([]models.Threat, error) {
	if len(p.targets) == 0 {
		return nil, nil
	}
	out := make([]models.Threat, 0, len(p.targets))

	for _, target := range p.targets {
		indicatorType := "domain"
		if ip := net.ParseIP(target); ip != nil {
			if ip.To4() != nil {
				indicatorType = "IPv4"
			} else {
				indicatorType = "IPv6"
			}
		}

		var result otxResponse
		endpoint := fmt.Sprintf("https://otx.alienvault.com/api/v1/indicators/%s/%s/general", indicatorType, target)
		resp, err := p.client.R().
			SetContext(ctx).
			SetHeader("X-OTX-API-KEY", p.apiKey).
			SetResult(&result).
			Get(endpoint)
		if err != nil {
			return nil, fmt.Errorf("otx request failed for %s: %w", target, err)
		}
		if resp.IsError() {
			return nil, fmt.Errorf("otx returned error for %s: %s", target, resp.Status())
		}

		iocType := "domain"
		if net.ParseIP(target) != nil {
			iocType = "ip"
		}

		out = append(out, models.Threat{
			IOCValue:    target,
			IOCType:     iocType,
			SourceName:  p.Name(),
			SourceURL:   endpoint,
			SourceQuery: target,
			RawEvidence: map[string]any{
				"pulse_count": result.PulseInfo.Count,
			},
			CollectedAt:   time.Now().UTC(),
			Corroboration: result.PulseInfo.Count,
		})
	}

	return out, nil
}
