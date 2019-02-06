# Project Sage

Analyze usage of a Black Duck system and offer sage advice for how to improve that usage to get the most value out of the product. Identifies issues which represent poor practices and/or areas where best practices could/should be applied.

## Goals

* Detect bad scanning practices which will result in poor system performance and/or inaccurate analysis results
* Detect and score usage of the system in terms of leveraging features that help organizations deal with security vulnerabilities or that will improve the overall value the system provides
  * Are Owners assigned to projects so that in the event there is a new vulnerability published, security leaders know who to contact if the project is affected?
  * Do project-versions have their Phase set (to something other than the default) indicating a differentiation between scans of development versions versus production or distributed versions?
  * Do project-versions have a license set (other than the default) that would allow proper interpretation of license compliance?
  * Does
* Easy to run
* Easy to understand guidance
* Easy to share results

# How to Run and Get Results

Sage is built as a docker image and is meant to either be run one-time (spot check) or as a service attached to a running Black Duck instance. 

When run once as a spot check, sage runs and dumps its results into a json-formatted file for review, sharing. If run as a service, sage runs on a pre-configured schedule (default: once/day) and accumulates information that is summarized each day into a json-formatted file for reviewing, sharing. If running as a service, sage will look at time-series information to produce better observations.

## Command to run one-time

```bash
mkdir /tmp/sage
docker run -v /tmp/sage:/var/log/sage gsnyderbds/sage
```

## Command to run as a service, detached from cluster

```bash
mkdir /tmp/sage
docker run -d -v /tmp/sage:/var/log/sage gsnyderbds/sage
```

## Running as a service as part of docker swarm cluster

TBD