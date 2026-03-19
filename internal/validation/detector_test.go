package validation

import (
	"testing"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func TestDetect_QuarantinesSingleSourceFreshDomain(t *testing.T) {
	now := time.Now().UTC()
	rec := models.ThreatRecord{
		IOCType:            "domain",
		IOCValue:           "paypal-secure-4821.com",
		CorroborationCount: 1,
		RawEvidenceJSON:    `{"domain_age_days":0}`,
		CollectedAt:        now,
		CreatedAt:          now,
	}

	out := Detect(rec)
	if out.PipelineStage != "quarantined" {
		t.Fatalf("expected quarantined, got %s", out.PipelineStage)
	}
	if out.DetectionRule != RuleSingleSourceFreshDomain {
		t.Fatalf("expected rule %s, got %s", RuleSingleSourceFreshDomain, out.DetectionRule)
	}
	if out.PoisonDetected == nil || !*out.PoisonDetected {
		t.Fatalf("expected poison_detected=true")
	}
}

func TestDetect_EmptyEvidenceVariantsQuarantineSuspiciousTimestamp(t *testing.T) {
	now := time.Now().UTC()
	for _, evidence := range []string{"", "   ", "{}", "null", "[]"} {
		rec := models.ThreatRecord{
			IOCType:            "ip",
			IOCValue:           "203.0.113.4",
			CorroborationCount: 5,
			RawEvidenceJSON:    evidence,
			CollectedAt:        now,
			CreatedAt:          now,
		}
		out := Detect(rec)
		if out.PipelineStage != "quarantined" {
			t.Fatalf("evidence %q: expected quarantined, got %s", evidence, out.PipelineStage)
		}
		if out.DetectionRule != RuleSuspiciousTimestamp {
			t.Fatalf("evidence %q: expected rule %s, got %s", evidence, RuleSuspiciousTimestamp, out.DetectionRule)
		}
	}
}

func TestDetect_QuarantinesTTPBannerMismatch(t *testing.T) {
	now := time.Now().UTC()
	rec := models.ThreatRecord{
		IOCType:            "ip",
		IOCValue:           "198.51.100.42",
		CorroborationCount: 3,
		OpenPorts:          []int{80, 50050},
		RawEvidenceJSON:    `{"banner":"Cloudflare edge node"}`,
		CollectedAt:        now,
		CreatedAt:          now,
	}

	out := Detect(rec)
	if out.PipelineStage != "quarantined" {
		t.Fatalf("expected quarantined, got %s", out.PipelineStage)
	}
	if out.DetectionRule != RuleTTPBannerMismatch {
		t.Fatalf("expected rule %s, got %s", RuleTTPBannerMismatch, out.DetectionRule)
	}
}

func TestDetect_QuarantinesSuspiciousTimestamp(t *testing.T) {
	now := time.Now().UTC()
	rec := models.ThreatRecord{
		IOCType:            "domain",
		IOCValue:           "old-malicious.example",
		CorroborationCount: 3,
		RawEvidenceJSON:    `{"domain_age_days":365}`,
		CollectedAt:        now.Add(-30 * 24 * time.Hour),
		CreatedAt:          now,
	}

	out := Detect(rec)
	if out.PipelineStage != "quarantined" {
		t.Fatalf("expected quarantined, got %s", out.PipelineStage)
	}
	if out.DetectionRule != RuleSuspiciousTimestamp {
		t.Fatalf("expected rule %s, got %s", RuleSuspiciousTimestamp, out.DetectionRule)
	}
}

func TestDetect_ValidatesSafeRecord(t *testing.T) {
	now := time.Now().UTC()
	rec := models.ThreatRecord{
		IOCType:            "domain",
		IOCValue:           "benign-example.org",
		CorroborationCount: 4,
		RawEvidenceJSON:    `{"domain_age_days":120}`,
		CollectedAt:        now,
		CreatedAt:          now.Add(-2 * time.Hour),
	}

	out := Detect(rec)
	if out.PipelineStage != "validated" {
		t.Fatalf("expected validated, got %s", out.PipelineStage)
	}
	if out.DetectionRule != "" {
		t.Fatalf("expected empty detection rule, got %s", out.DetectionRule)
	}
	if out.PoisonDetected == nil || *out.PoisonDetected {
		t.Fatalf("expected poison_detected=false")
	}
}
