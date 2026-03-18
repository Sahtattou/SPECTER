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

func NewShodanProvider(apiKey string) *ShodanProvider {
	return &ShodanProvider{client: shodan.NewClient(nil, apiKey)}
}

func (p *ShodanProvider) Name() string { return "shodan" }

func (p *ShodanProvider) Collect(ctx context.Context) ([]models.Threat, error) {
	seedIPs := []string{"8.8.8.8"}
	out := make([]models.Threat, 0, len(seedIPs))

	for _, ip := range seedIPs {
		host, err := p.client.GetServicesForHost(ctx, ip, nil)
		if err != nil {
			return nil, fmt.Errorf("shodan lookup failed for %s: %w", ip, err)
		}
		openPorts := make([]int, 0, len(host.Ports))
		for _, port := range host.Ports {
			openPorts = append(openPorts, int(port))
		}
		out = append(out, models.Threat{
			IOCValue:    ip,
			IOCType:     "ip",
			SourceName:  p.Name(),
			SourceURL:   "https://api.shodan.io",
			SourceQuery: ip,
			RawEvidence: map[string]any{
				"os":          host.OS,
				"isp":         host.ISP,
				"org":         host.Organization,
				"hostnames":   host.Hostnames,
				"vulns":       host.Vulnerabilities,
				"last_update": host.LastUpdate,
			},
			CollectedAt:   time.Now().UTC(),
			OpenPorts:     openPorts,
			ASN:           host.ASN,
			Corroboration: 1,
		})
	}

	return out, nil
}
