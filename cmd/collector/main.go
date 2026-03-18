package main

import (
	"time"

	"github.com/sirupsen/logrus"
)

func main() {

	logger := logrus.New()
	logger.SetFormatter(&logrus.JSONFormatter{})

	logger.WithFields(
		logrus.Fields{
			"action":    "init",
			"timestamp": time.Now().Format(time.RFC3339),
		}).Info("initialize program")

	println("Engine start 200")

}
