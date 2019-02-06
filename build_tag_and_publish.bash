#!/bin/bash

# Build the docker image, tag it, and push it to the Docker Cloud repository
#
TAGS=$1

source ./docker_build_common.bash

build_tag_and_publish sage.dockerfile sage "${TAGS}"