package providers

import (
	"fmt"
	"net"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/go-resty/resty/v2"
)

type OTXResponse struct {
	PulseInfo struct {
		Count  int `json:"count"`
		Pulses []struct {
			Name string   `json:"name"`
			Tags []string `json:"tags"`
		} `json:"pulses"`
	} `json:"pulse_info"`
}

type OTXProvider struct {
	Client *resty.Client
	APIKey string
}

func InitOTXProvider(apiKey string) *OTXProvider {
	return &OTXProvider{
		Client: resty.New().SetTimeout(10 * time.Second),
		APIKey: apiKey,
	}
}

func (p *OTXProvider) Name() string { return "AlienVault OTX" }

func (p *OTXProvider) Fetch(target string) (*models.ThreatRecord, error) {
	indicatorType := "domain"
	ip := net.ParseIP(target)
	if ip != nil {
		if ip.To4() != nil {
			indicatorType = "IPv4"
		} else {
			indicatorType = "IPv6"
		}
	}

	var result OTXResponse

	endpoint := fmt.Sprintf("https://otx.alienvault.com/api/v1/indicators/%s/%s/general", indicatorType, target)

	resp, err := p.Client.R().
		SetHeader("X-OTX-API-KEY", p.APIKey).
		SetResult(&result).
		Get(endpoint)

	if err != nil {
		return nil, fmt.Errorf("otx request failed: %w", err)
	}

	if resp.IsError() {
		return nil, fmt.Errorf("otx returned error: %s", resp.Status())
	}

	isMalicious := false
	confidence := 0
	var allTags []string

	if result.PulseInfo.Count > 0 {
		isMalicious = true
		confidence = 70

		tagsMap := make(map[string]bool)
		for _, pulse := range result.PulseInfo.Pulses {
			for _, tag := range pulse.Tags {
				if !tagsMap[tag] {
					tagsMap[tag] = true
					allTags = append(allTags, tag)
				}
			}
		}
	}

	return &models.ThreatRecord{
		Source:      p.Name(),
		Target:      target,
		Confidence:  confidence,
		IsMalicious: isMalicious,
		LastSeen:    time.Now(),
		Details: map[string]interface{}{
			"pulse_count": result.PulseInfo.Count,
			"tags":        allTags,
		},
	}, nil
}

func (p *OTXProvider) Supports(target string) bool {
	return len(target) > 3 && strings.Contains(target, ".") || net.ParseIP(target) != nil
}
