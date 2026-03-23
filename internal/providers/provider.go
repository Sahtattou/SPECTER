package providers

import (
	"context"
	"errors"
	"strings"
	"time"

	"github.com/Sahtattou/SPECTER/pkg/models"
)

type Provider interface {
	Name() string
	Collect(ctx context.Context) ([]models.Threat, error)
}

type ErrorKind string

const (
	ErrorKindUnknown       ErrorKind = "unknown"
	ErrorKindTransient     ErrorKind = "transient"
	ErrorKindRateLimited   ErrorKind = "rate_limited"
	ErrorKindPermanentAuth ErrorKind = "permanent_auth"
)

type ProviderError struct {
	Kind       ErrorKind
	Err        error
	RetryAfter time.Duration
}

func (e *ProviderError) Error() string {
	if e == nil || e.Err == nil {
		return "provider error"
	}
	return e.Err.Error()
}

func (e *ProviderError) Unwrap() error {
	if e == nil {
		return nil
	}
	return e.Err
}

func NewProviderError(kind ErrorKind, err error) error {
	return NewProviderErrorWithRetry(kind, err, 0)
}

func NewProviderErrorWithRetry(kind ErrorKind, err error, retryAfter time.Duration) error {
	if err == nil {
		return nil
	}
	return &ProviderError{Kind: kind, Err: err, RetryAfter: retryAfter}
}

func RetryAfter(err error) time.Duration {
	var pe *ProviderError
	if errors.As(err, &pe) && pe != nil && pe.RetryAfter > 0 {
		return pe.RetryAfter
	}
	return 0
}

func ClassifyProviderError(err error) ErrorKind {
	if err == nil {
		return ErrorKindUnknown
	}

	var pe *ProviderError
	if errors.As(err, &pe) && pe != nil {
		if pe.Kind != "" {
			return pe.Kind
		}
	}

	msg := strings.ToLower(err.Error())
	if strings.Contains(msg, "429") ||
		strings.Contains(msg, "too many requests") ||
		strings.Contains(msg, "rate limit") {
		return ErrorKindRateLimited
	}

	if strings.Contains(msg, "requires membership") ||
		strings.Contains(msg, "membership or higher") ||
		strings.Contains(msg, "upgrade required") ||
		strings.Contains(msg, "premium") ||
		strings.Contains(msg, "forbidden") ||
		strings.Contains(msg, "unauthorized") ||
		strings.Contains(msg, "invalid api key") {
		return ErrorKindPermanentAuth
	}

	if strings.Contains(msg, "timeout") ||
		strings.Contains(msg, "deadline") ||
		strings.Contains(msg, "temporar") ||
		strings.Contains(msg, "service unavailable") ||
		strings.Contains(msg, "connection") {
		return ErrorKindTransient
	}

	return ErrorKindUnknown
}
