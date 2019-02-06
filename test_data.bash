#!/bin/bash

source /usr/local/bin/virtualenvwrapper.sh

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

	if [ -z "${scan_name}" ]; then
		detect --blackduck.url=https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com \
			--blackduck.username=sysadmin \
			--blackduck.password=blackduck \
			--blackduck.trust.cert=true \
			--detect.project.name=too-many-scans \
			--detect.project.version.name=1.0 \
			--detect.pip.requirements.path=requirements.txt \
			--detect.policy.check.fail.on.severities=ALL > detect.log 2>&1
	else
		detect --blackduck.url=https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com \
			--blackduck.username=sysadmin \
			--blackduck.password=blackduck \
			--blackduck.trust.cert=true \
			--detect.project.name=too-many-scans \
			--detect.project.version.name=1.0 \
			--detect.pip.requirements.path=requirements.txt \
			--detect.policy.check.fail.on.severities=ALL \
			--detect.code.location.name=${scan_name} > detect.log 2>&1
	fi
}

mkdir -p test_data/scans

cd test_data/scans

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