#!/bin/bash

source /usr/local/bin/virtualenvwrapper.sh

export PROJECT_NAME=${1:-too-many-scans}
export VERSION_NAME=${2:-1.0}
export CODE_LOC_NAME=$3

HUB_URL=https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com
API_TOKEN=$(cat ~/.bd_tokens/demo-server-token) # substitute path to your token here

# HUB_USERNAME=********
# HUB_PASSWORD=********

function create_venv_as_needed
{
	venv=sage_test_data
	look_for_venv=$(lsvirtualenv | grep ${venv})
	if [ -z "${look_for_venv}" ]; then
		mkvirtualenv ${venv} -p $(which python3) > /dev/null 2>&1
	fi
	echo $venv
}

function scan {
	project_name=${1:-too-many-scans}
	version_name=${2:-1.0}
	scan_name=${3:-""}

	detect_options="--blackduck.url=${HUB_URL} \
			--blackduck.api.token=${API_TOKEN} \
			--blackduck.trust.cert=true \
			--detect.tools=DETECTOR \
			--detect.project.name=${project_name} \
			--detect.project.version.name=${version_name} \
			--detect.wait.for.results=true"

	if [ -f requirements.txt ]; then
		detect_options="${detect_options} --detect.pip.requirements.path=requirements.txt"
	fi

	if [ ! -z "${scan_name}" ]; then
		detect_options="${detect_options} --detect.code.location.name=${scan_name}"
	fi

	echo "Running: detect ${detect_options}"
	bash <(curl -s -L https://detect.synopsys.com/detect.sh) ${detect_options} >> detect.log 2>&1

	if [ $? -eq 0 ] || [ $? -e 3 ]; then
		echo "detect SUCCEEDED"
	else
		echo "detect FAILED"
	fi
}

function too-many-scans {
	oss_python_component=('Django==1.9.1' 'Django==1.9.2' 'Django==1.9.3' 'Django==1.9.4' 'Django==1.9.5' 'Django==1.9.6' 'Django==1.9.7' 'Django==1.9.8' 'Django==1.9.9' 'Django==2.1' 'Django==2.1.8')
	compononent_index=0
	for build_num in $(seq 1 ${#oss_python_component[@]})
	do
		venv=$(create_venv_as_needed)
		echo "======================================================"
		echo "Virtual env: ${venv}"
		dir_name="build_${build_num}"
		oss_component=${oss_python_component[$compononent_index]}
		echo "Setting up ${dir_name} to do scan using ${oss_component}"
		mkdir -p $dir_name
		cd $dir_name
		echo ${oss_component} > requirements.txt
		workon ${venv}
		pip install -r requirements.txt > pip_install.log 2>&1
		echo "-----"
		echo "Build environment has following python packages installed"
		echo "-----"
		pip freeze
		echo "-----"
		echo "Running detect to produce scan for ${dir_name}"
		if [ -z "${CODE_LOC_NAME}" ]; then
			echo "No code location (scan) name provided, so detect will make up a name based on the folder path"
			scan ${PROJECT_NAME} ${VERSION_NAME}
		else
			echo "A code location (scan) name provided (${CODE_LOC_NAME} so scans will over-write previous results"
			scan ${PROJECT_NAME} ${VERSION_NAME} ${CODE_LOC_NAME}
		fi
		deactivate
		cd ..
		rmvirtualenv ${venv}
		compononent_index=$(expr $compononent_index + 1)
		echo "======================================================"
	done	
}
mkdir -p test_data/scans/${PROJECT_NAME}

cd test_data/scans/${PROJECT_NAME}

too-many-scans
