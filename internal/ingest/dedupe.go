package ingest

import (
	"crypto/sha256"
	"encoding/hex"
	"strings"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func DedupeHash(r models.ThreatRecord) string {
	key := strings.ToLower(strings.Join([]string{
		r.IOCType,
		r.IOCValue,
		r.SourceName,
	}, "|"))
	sum := sha256.Sum256([]byte(key))
	return hex.EncodeToString(sum[:])
}
