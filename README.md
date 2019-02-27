# Project Sage

Analyze usage of a Black Duck system and offer sage advice for how to improve that usage to get the most value out of the product. Identifies issues which represent poor practices and/or areas where best practices could/should be applied.

## Table Of Contents

- [Goals](#goals)
- [How to Run and Get Results](#run)
  -  [Command to run one-time](#one-time)
    - [Sample Output](#one-time-sample-output)
- [Release History](#release-history)

## Goals <a name="goals"/>

* Detect bad scanning practices which will result in poor system performance and/or inaccurate analysis results
* Detect and score usage of the system in terms of leveraging features that help organizations deal with security vulnerabilities or that will improve the overall value the system provides
  * Are Owners assigned to projects so that in the event there is a new vulnerability published, security leaders know who to contact if the project is affected?
  * Do project-versions have their Phase set (to something other than the default) indicating a differentiation between scans of development versions versus production or distributed versions?
  * Do project-versions have a license set (other than the default) that would allow proper interpretation of license compliance?
  * Does
* Easy to run
* Easy to understand guidance
* Easy to share results

# How to Run and Get Results <a name="run" />

Sage is built as a docker image and is meant to either be run one-time (spot check) or as a service attached to a running Black Duck instance (**service implementation not available yet**). 

When run once as a spot check, sage runs and dumps its results into a json-formatted file for review, sharing. 

If run as a service, sage runs on a pre-configured schedule (default: once/day) and accumulates information that is summarized each day into a json-formatted file for reviewing, sharing. If running as a service, sage will look at time-series information to produce better observations.

## Command to run one-time <a name="one-time" />

You need to generate an api-token from an account that has appropriate access (e.g. sysadmin). Then,

```bash
mkdir /tmp/sage
docker run -v /tmp/sage:/var/log gsnyderbds/sage -h # will produce help
docker run -v /tmp/sage:/var/log gsnyderbds/sage <hub-url> <api-token>
```

Your results will be written to /tmp/sage directory.

You can interrupt sage with <ctrl>-c (to send SIGINT) and it will write the results it has accumulated to the specified file. Running sage with the --resume option will cause sage to read the file and resume the analysis where it left off.

### Sample Output <a name="one-time-sample-output" />

Here's a sample of what you can expect to see when you run sage:

```bash
$ docker run -v /tmp/sage:/var/log gsnyderbds/sage https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com `cat .sage.api.token`
2019-02-22 11:32:03,236:DEBUG:Took 0.2191791534423828 seconds to retrieve the 7 projects found on this instance of Black Duck
2019-02-22 11:32:03,236:DEBUG:Analyzing project microservice-strategy1
2019-02-22 11:32:03,432:DEBUG:Analyzing version 3 for project microservice-strategy1
2019-02-22 11:32:03,596:DEBUG:Analyzing version 4 for project microservice-strategy1
2019-02-22 11:32:03,765:DEBUG:Analyzing project microservice-strategy2
2019-02-22 11:32:03,938:DEBUG:Analyzing version LATEST for project microservice-strategy2
2019-02-22 11:32:04,100:DEBUG:Analyzing project my-project
2019-02-22 11:32:04,269:DEBUG:Analyzing version protex_bom_import for project my-project
2019-02-22 11:32:04,426:DEBUG:Analyzing project npm
2019-02-22 11:32:04,596:DEBUG:Analyzing version 1.0 for project npm
2019-02-22 11:32:04,749:DEBUG:Analyzing project struts2-showcase
2019-02-22 11:32:04,922:DEBUG:Analyzing version 2.6-SNAPSHOT for project struts2-showcase
2019-02-22 11:32:05,091:DEBUG:Analyzing project too-many-scans
2019-02-22 11:32:05,271:DEBUG:Analyzing version 1.0 for project too-many-scans
2019-02-22 11:32:05,509:DEBUG:Analyzing project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:06,170:DEBUG:Analyzing version 0 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:07,440:DEBUG:Analyzing version 1 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:07,981:DEBUG:Analyzing version 10 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:08,664:DEBUG:Analyzing version 11 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:09,344:DEBUG:Analyzing version 12 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:09,505:DEBUG:Analyzing version 13 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:09,657:DEBUG:Analyzing version 14 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:09,809:DEBUG:Analyzing version 15 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:09,961:DEBUG:Analyzing version 16 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:10,118:DEBUG:Analyzing version 17 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:10,275:DEBUG:Analyzing version 18 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:10,429:DEBUG:Analyzing version 19 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:10,583:DEBUG:Analyzing version 2 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:10,736:DEBUG:Analyzing version 3 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:10,889:DEBUG:Analyzing version 4 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:11,041:DEBUG:Analyzing version 5 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:11,194:DEBUG:Analyzing version 6 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:11,316:DEBUG:Analyzing version 7 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:11,468:DEBUG:Analyzing version 8 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:11,619:DEBUG:Analyzing version 9 for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:11,775:DEBUG:Analyzing version Default Version for project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b
2019-02-22 11:32:12,195:DEBUG:Writing results to /var/log/sage_says.json
2019-02-22 11:32:12,197:INFO:Wrote results to /var/log/sage_says.json
```

Here are the 'keys' in the JSON output from sage:

```bash
$ cat /tmp/sage/sage_says.json | jq 'keys'
[
  "hub_url",
  "other_issues",
  "suspect_projects",
  "suspect_versions",
  "unmapped_scans"
]

```

# Release History <a name="release-history" />

Feb 27, 2019

Added support for interrupting and resuming analysis. You can send SIGINT (2) or SIGTERM (15) and a signal handler will write the results out to the file specified. If you then restart with the --resume option, sage will read the file and resume where the analysis left off. This is particularly important when running sage on systems that have too much data or not enough resources and the analysis goes really slow.