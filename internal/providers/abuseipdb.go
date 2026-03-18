package providers

import (
	"context"
	"fmt"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/go-resty/resty/v2"
)

type abuseIPDBResponse struct {
	Data struct {
		IPAddress            string `json:"ipAddress"`
		AbuseConfidenceScore int    `json:"abuseConfidenceScore"`
		CountryCode          string `json:"countryCode"`
		ISP                  string `json:"isp"`
		Domain               string `json:"domain"`
		TotalReports         int    `json:"totalReports"`
	} `json:"data"`
}

type AbuseIPDBProvider struct {
	apiKey string
	client *resty.Client
}

func NewAbuseIPDBProvider(apiKey string) *AbuseIPDBProvider {
	return &AbuseIPDBProvider{
		apiKey: apiKey,
		client: resty.New().SetTimeout(10 * time.Second),
	}
}

func (p *AbuseIPDBProvider) Name() string { return "abuseipdb" }

func (p *AbuseIPDBProvider) Collect(ctx context.Context) ([]models.Threat, error) {
	seedIPs := []string{"8.8.8.8"}
	out := make([]models.Threat, 0, len(seedIPs))

	for _, ip := range seedIPs {
		var result abuseIPDBResponse
		resp, err := p.client.R().
			SetContext(ctx).
			SetHeader("Key", p.apiKey).
			SetHeader("Accept", "application/json").
			SetQueryParam("maxAgeInDays", "90").
			SetQueryParam("ipAddress", ip).
			SetResult(&result).
			Get("https://api.abuseipdb.com/api/v2/check")
		if err != nil {
			return nil, fmt.Errorf("abuseipdb request failed for %s: %w", ip, err)
		}
		if resp.IsError() {
			return nil, fmt.Errorf("abuseipdb returned error for %s: %s", ip, resp.Status())
		}

		out = append(out, models.Threat{
			IOCValue:    ip,
			IOCType:     "ip",
			SourceName:  p.Name(),
			SourceURL:   "https://api.abuseipdb.com/api/v2/check",
			SourceQuery: ip,
			RawEvidence: map[string]any{
				"abuse_confidence_score": result.Data.AbuseConfidenceScore,
				"country_code":           result.Data.CountryCode,
				"isp":                    result.Data.ISP,
				"domain":                 result.Data.Domain,
				"total_reports":          result.Data.TotalReports,
			},
			CollectedAt:   time.Now().UTC(),
			Corroboration: 1,
		})
	}

	return out, nil
}
