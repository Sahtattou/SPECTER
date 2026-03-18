package providers

import (
	"context"
	"fmt"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/ns3777k/go-shodan/v4/shodan"
)

type ShodanProvider struct {
	client *shodan.Client
}

func InitShodanProvider(apiKey string) *ShodanProvider {
	return &ShodanProvider{
		client: shodan.NewClient(nil, apiKey),
	}
}

func (s *ShodanProvider) Name() string { return "shodan" }

func (s *ShodanProvider) Fetch(ip string) (*models.ThreatRecord, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	host, err := s.client.GetServicesForHost(ctx, ip, nil)
	if err != nil {
		return nil, fmt.Errorf("shodan lookup failed: %w", err)
	}

	return &models.ThreatRecord{
		Source:      s.Name(),
		Target:      ip,
		IsMalicious: false,
		LastSeen:    time.Now(),
		Details: map[string]interface{}{
			"os":              host.OS,
			"ports":           host.Ports,
			"isp":             host.ISP,
			"org":             host.Organization,
			"hostnames":       host.Hostnames,
			"Vulnerabilities": host.Vulnerabilities,
			"ASN":             host.ASN,
			"LastUpdate":      host.LastUpdate,
		}}, nil
}

func (p *ShodanProvider) Supports(targetType string) bool {
	return targetType == "ip"
}
