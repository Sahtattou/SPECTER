package providers

import (
	"fmt"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/go-resty/resty/v2"
)

type CrtShEntry struct {
	IssuerName string `json:"issuer_name"`
	CommonName string `json:"common_name"`
	NameValue  string `json:"name_value"`
}

type CrtShProvider struct {
	Client *resty.Client
}

func InitCrtShProvider() *CrtShProvider {
	return &CrtShProvider{
		Client: resty.New().SetTimeout(45 * time.Second),
	}
}

func (p *CrtShProvider) Name() string { return "crt.sh" }

func (p *CrtShProvider) Fetch(target string) (*models.ThreatRecord, error) {
	var result []CrtShEntry

	resp, err := p.Client.R().
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

	subdomains := make(map[string]bool)

	for _, entry := range result {
		names := strings.Split(entry.NameValue, "\n")
		for _, name := range names {
			cleanName := strings.TrimSpace(name)

			cleanName = strings.ReplaceAll(cleanName, "*.", "")

			if cleanName != "" {
				subdomains[cleanName] = true
			}
		}
	}

	var uniqueSubdomains []string
	for sub := range subdomains {
		uniqueSubdomains = append(uniqueSubdomains, sub)
	}

	return &models.ThreatRecord{
		Source:      p.Name(),
		Target:      target,
		Confidence:  0,
		IsMalicious: false,
		LastSeen:    time.Now(),
		Details: map[string]interface{}{
			"certificates_found": len(result),
			"unique_subdomains":  uniqueSubdomains,
			"subdomain_count":    len(uniqueSubdomains),
		},
	}, nil
}
