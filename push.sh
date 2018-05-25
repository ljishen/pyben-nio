#!/usr/bin/env bash
#
# Execute this script after the building by Travis CI and Docker Hub
# successfully completed.
#
# References: [Create and use multi-architecture docker images](https://developer.ibm.com/linuxonpower/2017/07/27/create-multi-architecture-docker-image/)
#
# We might integrate this process to .travis.yml after the `docker manifest`
# command graduated from experimentation.

set -eu -o pipefail

IMAGE_NAME=ljishen/pyben-nio

docker manifest create "${IMAGE_NAME}" "${IMAGE_NAME}":amd64 "${IMAGE_NAME}":arm64v8
docker manifest annotate "${IMAGE_NAME}" "${IMAGE_NAME}":amd64 --os linux --arch amd64
docker manifest annotate "${IMAGE_NAME}" "${IMAGE_NAME}":arm64v8 --os linux --arch arm64 --variant v8

# purge the local manifest after push so that I can
# upgrade the manifest by creating a new one next time.
# https://github.com/docker/for-win/issues/1770
docker manifest push --purge "${IMAGE_NAME}"
