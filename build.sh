#!/usr/bin/env bash

IMAGE_ID=goaldsl

docker build -t ${IMAGE_ID} $@ .
