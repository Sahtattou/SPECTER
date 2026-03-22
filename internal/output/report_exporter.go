package output

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

func ExportReport(records []models.ThreatRecord) (string, error) {
	ts := time.Now().UTC().Format("20060102_150405")
	dir := "artifacts/reports"
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}
	outPath := filepath.Join(dir, fmt.Sprintf("specter_report_%s.pdf", ts))

	summary := buildSummary(records)
	pdf, err := buildVisualPDF(summary)
	if err != nil {
		return "", err
	}

	if err := os.WriteFile(outPath, pdf, 0o644); err != nil {
		return "", err
	}

	return outPath, nil
}

type reportSummary struct {
	GeneratedAt          string
	Total                int
	RealTelemetry        int
	Injected             int
	Validated            int
	Quarantined          int
	Detected             int
	Missed               int
	TopQuarantined       []models.ThreatRecord
	TopValidatedOrScored []models.ThreatRecord
}

func buildSummary(records []models.ThreatRecord) reportSummary {
	summary := reportSummary{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Total:       len(records),
	}

	quarantined := make([]models.ThreatRecord, 0)
	validated := make([]models.ThreatRecord, 0)

	for _, r := range records {
		if r.IsSynthetic {
			summary.Injected++
		} else {
			summary.RealTelemetry++
		}

		switch r.PipelineStage {
		case "quarantined":
			summary.Quarantined++
			quarantined = append(quarantined, r)
		case "validated", "scored":
			summary.Validated++
			validated = append(validated, r)
		}

		if r.PoisonDetected != nil {
			if *r.PoisonDetected {
				summary.Detected++
			} else if r.IsSynthetic {
				summary.Missed++
			}
		}
	}

	sortRecordsByPriority(quarantined)
	sortRecordsByPriority(validated)

	summary.TopQuarantined = takeTop(quarantined, 5)
	summary.TopValidatedOrScored = takeTop(validated, 5)
	return summary
}

func sortRecordsByPriority(records []models.ThreatRecord) {
	sort.Slice(records, func(i, j int) bool {
		si := scoreValue(records[i])
		sj := scoreValue(records[j])
		if si == sj {
			return records[i].CollectedAt.After(records[j].CollectedAt)
		}
		return si > sj
	})
}

func scoreValue(r models.ThreatRecord) float64 {
	if r.CompositeScore == nil {
		return 0
	}
	return *r.CompositeScore
}

func takeTop(records []models.ThreatRecord, n int) []models.ThreatRecord {
	if len(records) <= n {
		return records
	}
	return records[:n]
}

func safeText(input string) string {
	trimmed := strings.TrimSpace(input)
	if trimmed == "" {
		return "n/a"
	}
	return trimmed
}

func buildVisualPDF(summary reportSummary) ([]byte, error) {
	var content bytes.Buffer

	writeText(&content, 40, 770, "F2", 20, "SPECTER Threat Report")
	writeText(&content, 40, 750, "F1", 10, "Blue vs Red adversarial validation overview")
	writeText(&content, 420, 770, "F1", 9, "Generated:")
	writeText(&content, 420, 757, "F1", 9, safeText(summary.GeneratedAt))

	drawFilledRect(&content, 38, 662, 536, 72, 0.95)
	writeText(&content, 48, 715, "F2", 11, "Legend")
	writeText(&content, 48, 698, "F1", 9, "Origin: Real telemetry | Injected simulation")
	writeText(&content, 48, 684, "F1", 9, "Detector verdict: Detected (Quarantined) | Passed Validation | Missed Injection | Needs Review")
	writeText(&content, 48, 670, "F1", 9, "Action: Investigate quarantined high-score events first; tune rules for missed injections")

	drawMetricCard(&content, 40, 610, 120, 42, "Total", fmt.Sprintf("%d", summary.Total))
	drawMetricCard(&content, 172, 610, 120, 42, "Real", fmt.Sprintf("%d", summary.RealTelemetry))
	drawMetricCard(&content, 304, 610, 120, 42, "Injected", fmt.Sprintf("%d", summary.Injected))
	drawMetricCard(&content, 436, 610, 120, 42, "Detected", fmt.Sprintf("%d", summary.Detected))
	drawMetricCard(&content, 40, 560, 120, 42, "Validated", fmt.Sprintf("%d", summary.Validated))
	drawMetricCard(&content, 172, 560, 120, 42, "Quarantined", fmt.Sprintf("%d", summary.Quarantined))
	drawMetricCard(&content, 304, 560, 120, 42, "Missed", fmt.Sprintf("%d", summary.Missed))

	writeText(&content, 40, 530, "F2", 11, "Top Quarantined Highlights")
	drawTableHeader(&content, 40, 514)
	writeRecordRows(&content, 40, 498, summary.TopQuarantined)

	writeText(&content, 40, 405, "F2", 11, "Top Validated/Scored Highlights")
	drawTableHeader(&content, 40, 389)
	writeRecordRows(&content, 40, 373, summary.TopValidatedOrScored)

	writeText(&content, 40, 80, "F1", 8, "SPECTER report semantics match dashboard labels for jury consistency.")

	type obj struct {
		num  int
		body string
	}

	objects := []obj{
		{num: 1, body: "<< /Type /Catalog /Pages 2 0 R >>"},
		{num: 2, body: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>"},
		{num: 3, body: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>"},
		{num: 4, body: fmt.Sprintf("<< /Length %d >>\nstream\n%sendstream", content.Len(), content.String())},
		{num: 5, body: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"},
		{num: 6, body: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"},
	}

	var out bytes.Buffer
	out.WriteString("%PDF-1.4\n")

	offsets := make([]int, len(objects)+1)
	for _, o := range objects {
		offsets[o.num] = out.Len()
		_, _ = fmt.Fprintf(&out, "%d 0 obj\n%s\nendobj\n", o.num, o.body)
	}

	xrefPos := out.Len()
	_, _ = fmt.Fprintf(&out, "xref\n0 %d\n", len(objects)+1)
	out.WriteString("0000000000 65535 f \n")
	for i := 1; i <= len(objects); i++ {
		_, _ = fmt.Fprintf(&out, "%010d 00000 n \n", offsets[i])
	}
	_, _ = fmt.Fprintf(&out, "trailer\n<< /Size %d /Root 1 0 R >>\n", len(objects)+1)
	_, _ = fmt.Fprintf(&out, "startxref\n%d\n", xrefPos)
	out.WriteString("%%EOF\n")

	return out.Bytes(), nil
}

func drawFilledRect(buf *bytes.Buffer, x, y, w, h float64, gray float64) {
	_, _ = fmt.Fprintf(buf, "q %.2f g %.2f %.2f %.2f %.2f re f Q\n", gray, x, y, w, h)
}

func drawMetricCard(buf *bytes.Buffer, x, y, w, h float64, label, value string) {
	drawFilledRect(buf, x, y, w, h, 0.93)
	writeText(buf, x+8, y+h-14, "F1", 8, label)
	writeText(buf, x+8, y+12, "F2", 14, value)
}

func drawTableHeader(buf *bytes.Buffer, x, y float64) {
	drawFilledRect(buf, x, y-12, 536, 16, 0.90)
	writeText(buf, x+6, y-1, "F2", 8, "IOC")
	writeText(buf, x+220, y-1, "F2", 8, "Type")
	writeText(buf, x+270, y-1, "F2", 8, "Origin")
	writeText(buf, x+390, y-1, "F2", 8, "Verdict")
	writeText(buf, x+485, y-1, "F2", 8, "Score")
}

func writeRecordRows(buf *bytes.Buffer, x, startY float64, rows []models.ThreatRecord) {
	if len(rows) == 0 {
		writeText(buf, x+6, startY-2, "F1", 8, "No records in this section.")
		return
	}

	maxRows := 6
	if len(rows) > maxRows {
		rows = rows[:maxRows]
	}

	for i, r := range rows {
		y := startY - float64(i*16)
		ioc := truncateText(safeText(r.IOCValue), 34)
		origin := "Real telemetry"
		if r.IsSynthetic {
			origin = "Injected simulation"
		}
		verdict := verdictLabel(r)
		score := fmt.Sprintf("%.1f", scoreValue(r))

		writeText(buf, x+6, y, "F1", 8, ioc)
		writeText(buf, x+220, y, "F1", 8, safeText(r.IOCType))
		writeText(buf, x+270, y, "F1", 8, truncateText(origin, 20))
		writeText(buf, x+390, y, "F1", 8, truncateText(verdict, 20))
		writeText(buf, x+485, y, "F1", 8, score)
	}
}

func verdictLabel(r models.ThreatRecord) string {
	if r.PipelineStage == "quarantined" && r.PoisonDetected != nil && *r.PoisonDetected {
		return "Detected (Quarantined)"
	}
	if (r.PipelineStage == "validated" || r.PipelineStage == "scored") && r.PoisonDetected != nil && !*r.PoisonDetected {
		return "Passed Validation"
	}
	if r.IsSynthetic && r.PoisonDetected != nil && !*r.PoisonDetected {
		return "Missed Injection"
	}
	return "Needs Review"
}

func writeText(buf *bytes.Buffer, x, y float64, font string, size float64, text string) {
	_, _ = fmt.Fprintf(buf, "BT /%s %.2f Tf 1 0 0 1 %.2f %.2f Tm (%s) Tj ET\n", font, size, x, y, escapePDFText(text))
}

func truncateText(text string, max int) string {
	if max <= 0 || len(text) <= max {
		return text
	}
	if max <= 3 {
		return text[:max]
	}
	return text[:max-3] + "..."
}

func escapePDFText(input string) string {
	replacer := strings.NewReplacer(
		"\\", "\\\\",
		"(", "\\(",
		")", "\\)",
	)
	return replacer.Replace(input)
}
