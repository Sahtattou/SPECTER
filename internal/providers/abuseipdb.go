package providers

import (
	"fmt"
	"net"
	"net/http"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/go-resty/resty/v2"
)

type AbuseIPDBResponse struct {
	Data struct {
		IPAddress            string   `json:"ipAddress"`
		IsPublic             bool     `json:"isPublic"`
		IPVersion            int      `json:"ipVersion"`
		IsWhitelisted        bool     `json:"isWhitelisted"`
		AbuseConfidenceScore int      `json:"abuseConfidenceScore"`
		CountryCode          string   `json:"countryCode"`
		UsageType            string   `json:"usageType"`
		ISP                  string   `json:"isp"`
		Domain               string   `json:"domain"`
		Hostnames            []string `json:"hostnames"`
		IsTor                bool     `json:"isTor"`
		TotalReports         int      `json:"totalReports"`
		NumDistinctUsers     int      `json:"numDistinctUsers"`
		LastReportedAt       string   `json:"lastReportedAt"`
	} `json:"data"`
}

type AbuseIPDBProvider struct {
	APIKey     string
	HTTPClient *http.Client
}

func InitAbuseIPDBProvider(apiKey string) *AbuseIPDBProvider {
	return &AbuseIPDBProvider{
		APIKey:     apiKey,
		HTTPClient: &http.Client{Timeout: 10 * time.Second},
	}
}

func (p *AbuseIPDBProvider) Name() string { return "AbuseIPDB" }

func (p *AbuseIPDBProvider) Fetch(ip string) (*models.ThreatRecord, error) {

	if !p.Supports(ip) {
		return nil, fmt.Errorf("%s does not support target: %s", p.Name(), ip)
	}

	client := resty.New().SetTimeout(10 * time.Second)

	var result AbuseIPDBResponse

	resp, err := client.R().
		SetHeader("Key", p.APIKey).
		SetHeader("Accept", "application/json").
		SetQueryParam("maxAgeInDays", "90").
		SetQueryParam("ipAddress", ip).
		SetResult(&result).
		Get("https://api.abuseipdb.com/api/v2/check")

	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}

	if resp.IsError() {
		return nil, fmt.Errorf("abuseipdb error: %s", resp.Status())
	}

	data := result.Data

	return &models.ThreatRecord{
		Source:      p.Name(),
		Target:      ip,
		Confidence:  data.AbuseConfidenceScore,
		IsMalicious: data.AbuseConfidenceScore > 50,
		Details: map[string]interface{}{
			"is_public":          data.IsPublic,
			"ip_version":         data.IPVersion,
			"is_whitelisted":     data.IsWhitelisted,
			"country":            data.CountryCode,
			"usage_type":         data.UsageType,
			"isp":                data.ISP,
			"domain":             data.Domain,
			"hostnames":          data.Hostnames,
			"is_tor_node":        data.IsTor,
			"total_reports":      data.TotalReports,
			"num_distinct_users": data.NumDistinctUsers,
		},
	}, nil
}

func (p *AbuseIPDBProvider) Supports(target string) bool {
	return net.ParseIP(target) != nil
}
