package providers

import (
	"context"
	"fmt"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/go-resty/resty/v2"
)

type urlhausResponse struct {
	QueryStatus string `json:"query_status"`
	Urls        []struct {
		URLStatus string   `json:"url_status"`
		Threat    string   `json:"threat"`
		Tags      []string `json:"tags"`
	} `json:"urls"`
}

type URLHausProvider struct {
	apiKey string
	client *resty.Client
	hosts  []string
}

func NewURLHausProvider(apiKey string, hosts []string) *URLHausProvider {
	return &URLHausProvider{
		apiKey: apiKey,
		client: resty.New().SetTimeout(15 * time.Second).SetRetryCount(2),
		hosts:  hosts,
	}
}

func (p *URLHausProvider) Name() string { return "urlhaus" }

func (p *URLHausProvider) Collect(ctx context.Context) ([]models.Threat, error) {
	if len(p.hosts) == 0 {
		return nil, nil
	}
	out := make([]models.Threat, 0, len(p.hosts))

	for _, host := range p.hosts {
		var result urlhausResponse
		resp, err := p.client.R().
			SetContext(ctx).
			SetHeader("Auth-Key", p.apiKey).
			SetFormData(map[string]string{"host": host}).
			SetResult(&result).
			Post("https://urlhaus-api.abuse.ch/v1/host/")
		if err != nil {
			return nil, fmt.Errorf("urlhaus request failed for %s: %w", host, err)
		}
		if resp.IsError() {
			return nil, fmt.Errorf("urlhaus returned error for %s: %s", host, resp.Status())
		}

		corroboration := 0
		tags := make([]string, 0)
		onlineCount := 0
		for _, u := range result.Urls {
			corroboration++
			if u.URLStatus == "online" {
				onlineCount++
			}
			tags = append(tags, u.Tags...)
		}

		out = append(out, models.Threat{
			IOCValue:    host,
			IOCType:     "domain",
			SourceName:  p.Name(),
			SourceURL:   "https://urlhaus-api.abuse.ch/v1/host/",
			SourceQuery: host,
			RawEvidence: map[string]any{
				"query_status":       result.QueryStatus,
				"urls_total":         len(result.Urls),
				"urls_online":        onlineCount,
				"tags":               tags,
				"malware_indicators": corroboration,
			},
			CollectedAt:   time.Now().UTC(),
			Corroboration: corroboration,
		})
	}

	return out, nil
}
