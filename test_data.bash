#!/bin/bash

source /usr/local/bin/virtualenvwrapper.sh

HUB_URL=${1:-https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com}
HUB_USERNAME=${2:-sysadmin}
HUB_PASSWORD=${3:-blackduck}

function create_venv_as_needed
{
	venv=sage_test_data
	look_for_venv=$(lsvirtualenv | grep ${venv})
	if [ -z "${look_for_venv}" ]; then
		mkvirtualenv ${venv} > /dev/null 2>&1
	fi
	echo $venv
}

function scan {
	project_name=${1:-too-many-scans}
	version_name=${2:-1.0}
	scan_name=${3:-""}

	detect_options="--blackduck.url=${HUB_URL} \
			--blackduck.username=${HUB_USERNAME} \
			--blackduck.password=${HUB_PASSWORD} \
			--blackduck.trust.cert=true \
			--detect.project.name=${project_name} \
			--detect.project.version.name=${version_name} \
			--detect.pip.requirements.path=requirements.txt \
			--detect.policy.check.fail.on.severities=ALL"

	if [ -f requirements.txt ]; then
		detect_options="${detect_options} --detect.pip.requirements.path=requirements.txt"
	fi

	if [ ! -z "${scan_name}" ]; then
		detect_options="${detect_options} --detect.code.location.name=${scan_name}"
	fi

	echo "Running: detect ${detect_options}" > detect.log
	detect ${detect_options} >> detect.log 2>&1
}

function too-many-scans {
	oss_python_component=(six cycler decorator future datedeux pipfile urllib3 isodate pycparser docutils)
	compononent_index=0
	for build_num in $(seq 1 11)
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
		scan too-many-scans 1.0
		deactivate
		cd ..
		rmvirtualenv ${venv}
		compononent_index=$(expr $compononent_index + 1)
		echo "======================================================"
	done	
}
mkdir -p test_data/scans

cd test_data/scans

too-many-scans
