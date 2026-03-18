package storage

import "testing"

func TestRepositoryScaffold(t *testing.T) {
	r := Repository{}
	if (r != Repository{}) {
		t.Fatalf("unexpected repository scaffold state")
	}
}
