#!/usr/bin/env bash
#
# This script file generates Dockerfile-arm64v8

set -eu -o pipefail

PYTHON_VERSION=3.6
ALPINE_VERSION=3.7

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
desc_filename="$dir"/Dockerfile-arm64v8

source_url=https://raw.githubusercontent.com/docker-library/python/master/"${PYTHON_VERSION}"/alpine"${ALPINE_VERSION}"/Dockerfile

# Save url to file
curl -fsSL "$source_url" -o "$desc_filename"

sed -i "s/^FROM.*$/FROM multiarch\\/alpine:arm64-v${ALPINE_VERSION}/" "$desc_filename"
sed -i '/^CMD/d' "$desc_filename"

# Read the content of the base Dockerfile into variable
# https://stackoverflow.com/a/10771857
# shellcheck disable=SC2034
content=$(<"$dir"/Dockerfile)

# Remove the redundant header lines
content=$(sed '/^FROM/d' <<< "$content")
content=$(sed '/^MAINTAINER/d' <<< "$content")

# Generate the variable contains my own code
# Append the result to logic true to accept the non-zero exit status. See
#   https://unix.stackexchange.com/a/265151
read -r -d '' code <<-EOT || true

	# All previous lines of code are for installing Python $PYTHON_VERSION
	# Now add my own code
	$content
EOT

# Append my code to the final output
cat >>"$desc_filename" <<-EOT
	$code
EOT
