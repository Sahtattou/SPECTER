package providers

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
	"github.com/go-resty/resty/v2"
)

type crtShEntry struct {
	NameValue string `json:"name_value"`
}

type CRTShProvider struct {
	client         *resty.Client
	query          string
	deduplicate    bool
	excludeExpired bool
	maxResults     int
}

func NewCRTShProvider(query string, deduplicate bool, excludeExpired bool, maxResults int) *CRTShProvider {
	q := strings.TrimSpace(query)
	if maxResults < 0 {
		maxResults = 0
	}
	return &CRTShProvider{
		client:         resty.New().SetTimeout(45 * time.Second).SetRetryCount(2),
		query:          q,
		deduplicate:    deduplicate,
		excludeExpired: excludeExpired,
		maxResults:     maxResults,
	}
}

func (p *CRTShProvider) Name() string { return "crt.sh" }

func (p *CRTShProvider) Collect(ctx context.Context) ([]models.Threat, error) {
	if p.query == "" {
		return nil, nil
	}

	if deadline, ok := ctx.Deadline(); ok {
		_ = deadline
	}

	retryDelays := []time.Duration{0, 500 * time.Millisecond, 1500 * time.Millisecond}
	var resp *resty.Response
	var err error
	var result []crtShEntry

	for attempt, delay := range retryDelays {
		if attempt > 0 {
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(delay):
			}
		}

		result = nil
		req := p.client.R().
			SetContext(ctx).
			SetQueryParam("q", p.query).
			SetQueryParam("output", "json").
			SetResult(&result)
		if p.deduplicate {
			req.SetQueryParam("deduplicate", "Y")
		}
		if p.excludeExpired {
			req.SetQueryParam("exclude", "expired")
		}
		resp, err = req.Get("https://crt.sh/")
		if err != nil {
			if attempt == len(retryDelays)-1 {
				return nil, fmt.Errorf("crt.sh request failed: %w", err)
			}
			continue
		}

		if resp.StatusCode() == http.StatusTooManyRequests ||
			resp.StatusCode() == http.StatusServiceUnavailable ||
			resp.StatusCode() == http.StatusBadGateway ||
			resp.StatusCode() == http.StatusGatewayTimeout {
			if attempt == len(retryDelays)-1 {
				return nil, nil
			}
			continue
		}

		if resp.IsError() {
			return nil, fmt.Errorf("crt.sh returned error: %s", resp.Status())
		}
		break
	}

	target := p.query

	seen := make(map[string]struct{})
	threats := make([]models.Threat, 0, len(result))
	for _, entry := range result {
		names := strings.Split(entry.NameValue, "\n")
		for _, n := range names {
			domain := strings.TrimSpace(strings.TrimPrefix(n, "*."))
			if domain == "" {
				continue
			}
			if _, ok := seen[domain]; ok {
				continue
			}
			seen[domain] = struct{}{}
			threats = append(threats, models.Threat{
				IOCValue:    domain,
				IOCType:     "domain",
				SourceName:  p.Name(),
				SourceURL:   "https://crt.sh/",
				SourceQuery: target,
				RawEvidence: map[string]any{
					"name_value": entry.NameValue,
				},
				CollectedAt:   time.Now().UTC(),
				Corroboration: 1,
			})
			if p.maxResults > 0 && len(threats) >= p.maxResults {
				return threats, nil
			}
		}
	}

	return threats, nil
}
