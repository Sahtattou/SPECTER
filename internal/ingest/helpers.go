package ingest

import (
	"net"
	"net/url"
	"strings"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func DetectType(v string) string {
	s := strings.TrimSpace(v)
	if s == "" {
		return "unknown"
	}
	if net.ParseIP(s) != nil {
		return "ip"
	}
	if u, err := url.ParseRequestURI(s); err == nil && u.Scheme != "" && u.Host != "" {
		return "url"
	}
	if strings.Contains(s, ".") {
		return "domain"
	}
	return "unknown"
}

func BuildDedupeHash() string {
	return DedupeHash(models.ThreatRecord{
		IOCType:    "ip",
		IOCValue:   "1.2.3.4",
		SourceName: "seed",
	})
}
