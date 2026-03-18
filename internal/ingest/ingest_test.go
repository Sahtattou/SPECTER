package ingest

import "testing"

func TestIngestScaffold(t *testing.T) {
NormalizeThreatEvent()
BuildDedupeHash()
}
