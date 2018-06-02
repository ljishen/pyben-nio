#!/usr/bin/env bash
#
# This script file generates Dockerfile.arm64v8

set -eu -o pipefail

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
arch_dockerfile="$dir"/Dockerfile.arm64v8

# Read the content of the base Dockerfile into variable
# https://stackoverflow.com/a/10771857
# shellcheck disable=SC2034
content=$(<"$dir"/Dockerfile)

cat > "${arch_dockerfile}" <<- EOF
	#
	# NOTE: THIS DOCKERFILE IS GENERATED VIA "update.sh"
	#
	# PLEASE DO NOT EDIT IT DIRECTLY.
	#

	$content
EOF

sed -i "s/^FROM.*$/FROM resin\\/aarch64-alpine-python:3.6-slim/" "$arch_dockerfile"
