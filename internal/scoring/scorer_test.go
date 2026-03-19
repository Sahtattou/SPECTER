package scoring

import (
	"testing"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func TestScore_QuarantinedRemainsUnchanged(t *testing.T) {
	rec := models.ThreatRecord{PipelineStage: "quarantined"}
	out := Score(rec)
	if out.PipelineStage != "quarantined" {
		t.Fatalf("expected quarantined stage, got %s", out.PipelineStage)
	}
	if out.CompositeScore != nil {
		t.Fatalf("expected nil score for already quarantined record")
	}
}

func TestScore_PoisonDetectedForcesQuarantineAndZero(t *testing.T) {
	d := true
	rec := models.ThreatRecord{
		PipelineStage:      "validated",
		CorroborationCount: 1,
		PoisonDetected:     &d,
	}
	out := Score(rec)
	if out.PipelineStage != "quarantined" {
		t.Fatalf("expected quarantined stage, got %s", out.PipelineStage)
	}
	if out.CompositeScore == nil {
		t.Fatalf("expected non-nil score")
	}
	if *out.CompositeScore != 0 {
		t.Fatalf("expected clamped score 0, got %f", *out.CompositeScore)
	}
}

func TestScore_IsSyntheticPenaltyClampsToZero(t *testing.T) {
	rec := models.ThreatRecord{PipelineStage: "validated", IsSynthetic: true, CorroborationCount: 0}
	out := Score(rec)
	if out.CompositeScore == nil {
		t.Fatalf("expected non-nil score")
	}
	if *out.CompositeScore != 0 {
		t.Fatalf("expected score 0 after clamp, got %f", *out.CompositeScore)
	}
	if out.ThreatLevel != "low" {
		t.Fatalf("expected low threat level, got %s", out.ThreatLevel)
	}
}

func TestScore_PortBonusesAndThresholds(t *testing.T) {
	rec := models.ThreatRecord{
		PipelineStage:      "validated",
		CorroborationCount: 3,
		OpenPorts:          []int{8888, 3389},
	}
	out := Score(rec)
	if out.CompositeScore == nil {
		t.Fatalf("expected non-nil score")
	}
	want := 20.0 + 30.0 + 20.0 + 8.0 + 3.0
	if *out.CompositeScore != want {
		t.Fatalf("expected score %f, got %f", want, *out.CompositeScore)
	}
	if out.ThreatLevel != "critical" {
		t.Fatalf("expected critical threat level, got %s", out.ThreatLevel)
	}
}

func TestScore_DetectionRulePenaltyApplied(t *testing.T) {
	rec := models.ThreatRecord{
		PipelineStage:      "validated",
		CorroborationCount: 6,
		DetectionRule:      "SUSPICIOUS_TIMESTAMP",
	}
	out := Score(rec)
	if out.CompositeScore == nil {
		t.Fatalf("expected non-nil score")
	}
	want := 20.0 + 60.0 - 35.0
	if *out.CompositeScore != want {
		t.Fatalf("expected score %f, got %f", want, *out.CompositeScore)
	}
	if out.ThreatLevel != "medium" {
		t.Fatalf("expected medium threat level, got %s", out.ThreatLevel)
	}
}
