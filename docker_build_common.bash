#!/bin/bash

export DOCKER_CLOUD_USERNAME=gsnyderbds

function build_tag_and_publish()
{
	docker_file=$1
	repo=$2
	tags=$3		# comma-separated list of tags - no spaces - e.g. tag1,latest (default: latest)

	tags=${tags:-latest}

	export BUILD_TAG_OPTS=""

	##################
	# Build the image with the tag list
	##################
	IFS=',' read -r -a image_tags <<< "${tags}"
	for image_tag in "${image_tags[@]}"
	do
		BUILD_TAG_OPTS="${BUILD_TAG_OPTS} -t ${DOCKER_CLOUD_USERNAME}/${repo}:${image_tag}"
	done

	docker build ${BUILD_TAG_OPTS} -f ${docker_file} .

	##################
	# Publish the image for each tag supplied
	##################
	for image_tag in "${image_tags[@]}"
	do
		docker push ${DOCKER_CLOUD_USERNAME}/${repo}:${image_tag}
	done
}
