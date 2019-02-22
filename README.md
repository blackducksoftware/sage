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

Sage is built as a docker image and is meant to either be run one-time (spot check) or as a service attached to a running Black Duck instance (**service implementation not available yet**). 

When run once as a spot check, sage runs and dumps its results into a json-formatted file for review, sharing. 

If run as a service, sage runs on a pre-configured schedule (default: once/day) and accumulates information that is summarized each day into a json-formatted file for reviewing, sharing. If running as a service, sage will look at time-series information to produce better observations.

## Command to run one-time

You need to generate an api-token from an account that has appropriate access (e.g. sysadmin). Then,

```bash
mkdir /tmp/sage
docker run -v /tmp/sage:/var/log gsnyderbds/sage -h # will produce help
docker run -v /tmp/sage:/var/log gsnyderbds/sage <hub-url> <api-token>
```

Your results will be written to /tmp/sage directory.

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

And here is the output produced by the above command showing all the info collected:

```bash
$ cat /tmp/sage/sage_says.json | jq . | tee sage_says_prettified.json
{
  "hub_url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com",
  "other_issues": [],
  "unmapped_scans": {
    "message": "Unmapped scans represent scanning data that is not mapped to any project-version, and hence, they are potentially consuming space that should be reclaimed.",
    "scans": [
      {
        "name": "denada BOM",
        "createdAt": "2019-02-13T22:24:35.355Z",
        "scanSize": 0,
        "updatedAt": "2019-02-14T22:05:48.272Z",
        "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/1c6e659c-e3ab-395a-8cc7-a8b0cc904241"
      },
      {
        "name": "denada SCAN 2",
        "createdAt": "2019-02-13T22:24:48.886Z",
        "scanSize": 40377317,
        "updatedAt": "2019-02-14T22:05:44.618Z",
        "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/10a494de-314a-31e6-8978-2476d767166f"
      }
    ]
  },
  "suspect_projects": [
    {
      "name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "createdAt": "2019-02-13T21:36:24.200Z",
      "createdBy": "sysadmin",
      "updatedAt": "2019-02-13T21:36:24.267Z",
      "updatedBy": "sysadmin",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b has 21 versions which is greater than the recommend maximum of 20. There are 0 versions that have been released. There are 0 versions that have been archived. You should review these versions and remove extraneous ones, and their scans, to reclaim space and reduce clutter. Typically there should be one version per development branch, and one version per release. When new vulnerabilities are published you want to be able to quickly identify which projects are affected and take action. Keeping a large number of un-released versions in the system will make that difficult. And accruing a large number of versions per project can lead to serious performance degradation. Look at https://github.com/blackducksoftware/hub-rest-api-python/tree/master/examples for python examples for finding/deleting/removing versions and their scans"
    }
  ],
  "suspect_versions": [
    {
      "versionName": "1.0",
      "createdAt": "2019-02-21T16:05:47.470Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-21T16:07:43.745Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/049c1f41-22a9-4641-a976-c53213a3cbdb/versions/d2679aa4-0cce-4748-b257-2ca89b17d92f",
      "project_name": "npm",
      "message": "Project npm, version 1.0 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "1.0",
      "createdAt": "2019-02-09T19:05:50.435Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "DEVELOPMENT",
      "settingUpdatedAt": "2019-02-13T21:44:01.704Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/dcd5f221-319b-4f52-ba5d-16998cc3b907/versions/c2336a6a-097d-46d9-861c-4bbd91b948c7",
      "project_name": "too-many-scans",
      "message": "Project too-many-scans, version 1.0 has 22 scans which is greater than the maximum recommended versions of 20. Review the scans to make sure there are not redundant scans all mapped to this project version. Look for scans with similar names or sizes. If redundant scans are found, you should delete them and update the scanning setup to use --detect.code.location.name with hub-detect to override scan names and delete redundant scans.",
      "signature_scan_info": [
        {
          "name": "build_11/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:15:46.695Z",
          "scanSize": 24261,
          "updatedAt": "2019-02-13T21:44:01.709Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/8557f3f0-3a2d-3cba-aeb8-7a6afe3ea444",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_10/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:14:46.805Z",
          "scanSize": 24553,
          "updatedAt": "2019-02-13T21:43:01.416Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/4c9c6e99-5dd9-38e4-8f7d-77dc3ce4f4d9",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_9/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:13:46.587Z",
          "scanSize": 24381,
          "updatedAt": "2019-02-13T21:41:55.142Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/43fe9719-2d86-300d-aa02-16781bcf25da",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_8/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:12:46.367Z",
          "scanSize": 24761,
          "updatedAt": "2019-02-13T21:41:00.894Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/ba09262b-d08e-38bb-b6c1-ef416a7f02d2",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_7/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:11:46.095Z",
          "scanSize": 24535,
          "updatedAt": "2019-02-13T21:40:00.613Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/f2889782-2a08-3500-863c-783f084f532b",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_6/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:10:45.718Z",
          "scanSize": 24608,
          "updatedAt": "2019-02-13T21:39:00.339Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/e63db6c7-f382-3c32-81f4-d767db6b2bc0",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_5/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:09:46.097Z",
          "scanSize": 24380,
          "updatedAt": "2019-02-13T21:38:00.059Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/67960f09-92fd-3155-b7ca-0cebeadf1ebf",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_4/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:08:45.701Z",
          "scanSize": 24373,
          "updatedAt": "2019-02-13T21:36:59.799Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/fcb0f182-5e39-3719-8e87-8193c876b3ba",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_3/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:07:44.699Z",
          "scanSize": 24543,
          "updatedAt": "2019-02-13T21:35:59.532Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/41232579-2206-3233-91a6-81a53a84d9d8",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_2/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:06:55.416Z",
          "scanSize": 24759,
          "updatedAt": "2019-02-13T21:35:01.261Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/cc27583f-7b65-3fb6-875b-f80b8db4146c",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_1/too-many-scans/1.0 scan",
          "createdAt": "2019-02-09T19:06:05.221Z",
          "scanSize": 24846,
          "updatedAt": "2019-02-13T21:34:00.949Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/45a2fe5f-a09b-325f-b928-b4f1c27c2e9e",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        }
      ],
      "bom_scan_info": [
        {
          "name": "build_11//Users/gsnyder/Projects/sage/test_data/scans/build_11 pip/bom",
          "createdAt": "2019-02-09T19:15:32.352Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:43:41.586Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/d1be936f-b1ae-3101-aead-e01f07614e6d",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_10//Users/gsnyder/Projects/sage/test_data/scans/build_10 pip/bom",
          "createdAt": "2019-02-09T19:14:32.660Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:42:41.315Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/afbcdb1a-fbbe-3324-9c48-a77ac7972c53",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_9//Users/gsnyder/Projects/sage/test_data/scans/build_9 pip/bom",
          "createdAt": "2019-02-09T19:13:32.537Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:41:41.063Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/42bae923-f807-33c1-ad45-fe07fbe46e73",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_8//Users/gsnyder/Projects/sage/test_data/scans/build_8 pip/bom",
          "createdAt": "2019-02-09T19:12:32.305Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:40:36.763Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/19e4fe0a-4c38-319f-815d-22d2e30f2144",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_7//Users/gsnyder/Projects/sage/test_data/scans/build_7 pip/bom",
          "createdAt": "2019-02-09T19:11:32.119Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:39:40.516Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/e23ea468-37b7-35ac-909b-30d42e42186f",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_6//Users/gsnyder/Projects/sage/test_data/scans/build_6 pip/bom",
          "createdAt": "2019-02-09T19:10:31.998Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:38:40.233Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/cc48c7da-2a4c-349d-ab14-03d8a47d9841",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_5//Users/gsnyder/Projects/sage/test_data/scans/build_5 pip/bom",
          "createdAt": "2019-02-09T19:09:32.215Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:37:39.962Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/6e6938d5-3a78-3d17-aa0e-8465164785ae",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_4//Users/gsnyder/Projects/sage/test_data/scans/build_4 pip/bom",
          "createdAt": "2019-02-09T19:08:31.866Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:36:45.725Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/052f08a0-885b-3d5b-8ce6-dcafe290e528",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_3//Users/gsnyder/Projects/sage/test_data/scans/build_3 pip/bom",
          "createdAt": "2019-02-09T19:07:30.863Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:35:41.435Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/83932ab3-ceac-3fad-9ce0-13b3e5415c3d",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_2//Users/gsnyder/Projects/sage/test_data/scans/build_2 pip/bom",
          "createdAt": "2019-02-09T19:06:41.046Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:34:41.181Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/aed87a8c-905e-3e59-b366-07d0ef95d1b3",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        },
        {
          "name": "build_1//Users/gsnyder/Projects/sage/test_data/scans/build_1 pip/bom",
          "createdAt": "2019-02-09T19:05:51.372Z",
          "scanSize": 0,
          "updatedAt": "2019-02-13T21:33:41.039Z",
          "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/6d99dcc2-40c5-39e6-9c12-00be8470c492",
          "project_name": "too-many-scans",
          "version_name": "1.0"
        }
      ]
    },
    {
      "versionName": "0",
      "createdAt": "2019-02-13T21:36:24.695Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:24.695Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/82870792-9272-42ed-8481-c03586e87b7b",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 0 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "1",
      "createdAt": "2019-02-13T21:36:24.851Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:24.851Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/74741368-5174-4f78-ab9e-7dbe3e5dbda0",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 1 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "10",
      "createdAt": "2019-02-13T21:36:26.227Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:26.227Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/859f4b90-6e16-47a3-bbb1-0b2b9afffdf9",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 10 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "11",
      "createdAt": "2019-02-13T21:36:26.379Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:26.379Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/9ef16868-844c-48e1-9656-b66fa386d736",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 11 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "12",
      "createdAt": "2019-02-13T21:36:26.532Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:26.532Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/b5e5c1b9-b6d4-49bf-a348-18f2d66648bd",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 12 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "13",
      "createdAt": "2019-02-13T21:36:26.688Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:26.688Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/ec1ca5e7-4579-4c3f-9cdc-835937e12235",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 13 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "14",
      "createdAt": "2019-02-13T21:36:26.845Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:26.845Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/670afc99-600f-4e24-b86a-7b68c2f7f5fe",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 14 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "15",
      "createdAt": "2019-02-13T21:36:26.999Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:26.999Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/502358c3-4599-45ac-9820-a8bafd4abaa8",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 15 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "16",
      "createdAt": "2019-02-13T21:36:27.148Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:27.148Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/fbdd35c1-8739-4143-b47f-b5fed05a93d1",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 16 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "17",
      "createdAt": "2019-02-13T21:36:27.298Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:27.298Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/f803bb73-44b0-4034-85dc-84851ce2768c",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 17 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "18",
      "createdAt": "2019-02-13T21:36:27.446Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:27.446Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/3bf3b4d9-dd66-4184-814c-26e48ff29ab9",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 18 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "19",
      "createdAt": "2019-02-13T21:36:27.600Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:27.600Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/fb942480-a619-4ac1-ae63-8be446f910c0",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 19 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "2",
      "createdAt": "2019-02-13T21:36:25.004Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:25.004Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/7820a4ed-647b-4d0c-918d-dc6da2c2ceb0",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 2 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "3",
      "createdAt": "2019-02-13T21:36:25.153Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:25.153Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/16713910-edf7-4a6d-aadf-d8dbbb310b73",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 3 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "4",
      "createdAt": "2019-02-13T21:36:25.300Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:25.300Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/f98e9211-7944-4d37-981b-47b9cf93c1b4",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 4 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "5",
      "createdAt": "2019-02-13T21:36:25.454Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:25.454Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/53133667-eeba-4b7e-b5df-1a763fd7a179",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 5 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "6",
      "createdAt": "2019-02-13T21:36:25.605Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:25.605Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/fda27fca-fe12-44da-98f8-2cf609558614",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 6 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "7",
      "createdAt": "2019-02-13T21:36:25.770Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:25.770Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/94c582b4-fcd0-4ba8-891f-e0b132acd147",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 7 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "8",
      "createdAt": "2019-02-13T21:36:25.921Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:25.921Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/fe6a8d52-1c85-47b4-b215-753305277c73",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 8 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "9",
      "createdAt": "2019-02-13T21:36:26.077Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:26.077Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/9dec6ad6-2ee6-40bb-9e55-bc3b924e1b74",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version 9 has 0 scans. Should it be removed?"
    },
    {
      "versionName": "Default Version",
      "createdAt": "2019-02-13T21:36:24.247Z",
      "createdBy": "sysadmin",
      "distribution": "EXTERNAL",
      "phase": "PLANNING",
      "settingUpdatedAt": "2019-02-13T21:36:24.247Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/0cdd1ce6-67a8-46dd-a31c-c9cd77129a68/versions/92dbfe95-66c2-4cf4-b0c3-f59faaab2e00",
      "project_name": "too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b",
      "message": "Project too-many-versions-c2708b95-c6c1-4f1a-8de7-07f811cf817b, version Default Version has 0 scans. Should it be removed?"
    }
  ]
}

```

