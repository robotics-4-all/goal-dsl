#!/usr/bin/env bash

IMAGE_ID=telos

docker build -t ${IMAGE_ID} $@ .
