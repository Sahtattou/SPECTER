package providers

import (
	"fmt"
	"net"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/go-resty/resty/v2"
)

// 1. The JSON Structure for URLhaus
type URLhausResponse struct {
	QueryStatus string `json:"query_status"`
	Host        string `json:"host"`
	Urls        []struct {
		URLStatus string   `json:"url_status"`
		Threat    string   `json:"threat"`
		Tags      []string `json:"tags"`
	} `json:"urls"`
}

type URLhausProvider struct {
	Client *resty.Client
	APIKey string
}

func InitURLhausProvider(apiKey string) *URLhausProvider {
	return &URLhausProvider{
		Client: resty.New().SetTimeout(15*time.Second).SetRetryCount(2).SetHeader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
		APIKey: apiKey,
	}
}

func (p *URLhausProvider) Name() string { return "URLhaus" }

func (p *URLhausProvider) Fetch(target string) (*models.ThreatRecord, error) {
	var result URLhausResponse

	resp, err := p.Client.R().
		SetHeader("Auth-Key", p.APIKey).
		SetFormData(map[string]string{
			"host": target,
		}).
		SetResult(&result).
		Post("https://urlhaus-api.abuse.ch/v1/host/")

	if err != nil {
		return nil, fmt.Errorf("urlhaus request failed: %w", err)
	}

	if resp.IsError() {
		return nil, fmt.Errorf("urlhaus returned error: %s", resp.Status())
	}

	if result.QueryStatus != "ok" && result.QueryStatus != "no_results" {
		return nil, fmt.Errorf("urlhaus API error: %s", result.QueryStatus)
	}

	isMalicious := false
	confidence := 0
	activeMalwareUrls := 0
	tagsMap := make(map[string]bool)

	if result.QueryStatus == "ok" && len(result.Urls) > 0 {
		isMalicious = true
		confidence = 100

		for _, u := range result.Urls {
			if u.URLStatus == "online" {
				activeMalwareUrls++
			}
			for _, tag := range u.Tags {
				tagsMap[tag] = true
			}
		}
	}

	var uniqueTags []string
	for tag := range tagsMap {
		uniqueTags = append(uniqueTags, tag)
	}

	return &models.ThreatRecord{
		Source:      p.Name(),
		Target:      target,
		Confidence:  confidence,
		IsMalicious: isMalicious,
		LastSeen:    time.Now(),
		Details: map[string]interface{}{
			"total_malware_urls":  len(result.Urls),
			"active_malware_urls": activeMalwareUrls,
			"tags":                uniqueTags,
		},
	}, nil
}

func (p *URLhausProvider) Supports(target string) bool {
	isIP := net.ParseIP(target) != nil
	hasProtocol := strings.HasPrefix(target, "http")
	hasDot := strings.Contains(target, ".")

	return !isIP && (hasProtocol || hasDot)
}
