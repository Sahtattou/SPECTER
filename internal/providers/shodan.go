package providers

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/ns3777k/go-shodan/v4/shodan"
)

type ShodanProvider struct {
	client  *shodan.Client
	targets []string
}

func NewShodanProvider(apiKey string, targets []string) *ShodanProvider {
	return &ShodanProvider{client: shodan.NewClient(nil, apiKey), targets: targets}
}

func (p *ShodanProvider) Name() string { return "shodan" }

func (p *ShodanProvider) Collect(ctx context.Context) ([]models.Threat, error) {
	if len(p.targets) == 0 {
		return nil, nil
	}
	out := make([]models.Threat, 0, len(p.targets))

	for _, ip := range p.targets {
		host, err := p.client.GetServicesForHost(ctx, ip, nil)
		if err != nil {
			msg := strings.ToLower(err.Error())
			kind := ErrorKindTransient
			if strings.Contains(msg, "requires membership") ||
				strings.Contains(msg, "membership or higher") ||
				strings.Contains(msg, "forbidden") ||
				strings.Contains(msg, "unauthorized") ||
				strings.Contains(msg, "invalid api key") {
				kind = ErrorKindPermanentAuth
			} else if strings.Contains(msg, "too many requests") || strings.Contains(msg, "429") {
				kind = ErrorKindRateLimited
			}
			return nil, NewProviderError(kind, fmt.Errorf("shodan lookup failed for %s: %w", ip, err))
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
