package providers

import (
	"errors"
	"testing"
	"time"
)

func TestClassifyProviderErrorTyped(t *testing.T) {
	err := NewProviderError(ErrorKindPermanentAuth, errors.New("requires membership or higher"))
	if got := ClassifyProviderError(err); got != ErrorKindPermanentAuth {
		t.Fatalf("expected %s, got %s", ErrorKindPermanentAuth, got)
	}
}

func TestClassifyProviderErrorMessageFallback(t *testing.T) {
	err := errors.New("abuseipdb returned error: 429 Too Many Requests")
	if got := ClassifyProviderError(err); got != ErrorKindRateLimited {
		t.Fatalf("expected %s, got %s", ErrorKindRateLimited, got)
	}
}

func TestRetryAfterExtraction(t *testing.T) {
	retry := 7 * time.Minute
	err := NewProviderErrorWithRetry(ErrorKindRateLimited, errors.New("rate limit"), retry)
	if got := RetryAfter(err); got != retry {
		t.Fatalf("expected %s, got %s", retry, got)
	}
}
