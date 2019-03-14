# Project Sage

Analyze usage of a Black Duck system and offer sage advice for how to improve that usage to get the most value out of the product. Identifies issues which represent poor practices and/or areas where best practices could/should be applied.

## Table Of Contents

- [Goals](#goals)
- [How to Run and Get Results](#run)
- [Release History](#release-history)

## Goals <a name="goals"/>

* Detect bad scanning practices which will result in poor system performance and/or inaccurate analysis results
* Easy to run
* Easy to understand guidance
* Easy to share results

# How to Run and Get Results <a name="run" />

Sage uses:

- Python3
- An API token from your Black Duck server
  - The user account this token is issued from needs to have visibility to all the projects, versions, and scans you want to analyze, e.g. has role 'Systemadmin', 'Super User', or 'Global Code Scanner'
- Highly recommended: [virtualenv](https://virtualenv.pypa.io/en/latest/), [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)

Sage produces analysis outpout in json format so it's easy to read (using a tool like jq) and it's easy to use as input to the other tools which might want to act on the information.

To run,

```bash
mkvirtualenv sage # optional, but again, nice to use virtualenv and virtualenvwrapper
pip3 install -r requirements.txt
python3 sage.py -h # for help
python3 sage.py https://your-hub-dns {api-token}
```

Analysis output is writtent to `/var/log/sage_says.json`

What you can expect to get,

```bash
cat /var/log/sage_says.json | jq 'keys'
[
  "hub_url",
  "hub_version",
  "jobs_info",
  "other_issues",
  "projects_with_too_many_versions",
  "projects_without_an_owner",
  "projects_without_any_release",
  "reviewed_projects",
  "reviewed_versions",
  "time_of_analysis",
  "unmapped_scans",
  "versions_with_unusual_number_of_scans"
]

cat /var/log/sage_says.json | jq .projects_with_too_many_versions
[
  {
    "name": "too-many-versions-5e6a5320-1105-4f6f-8d18-39cda054b248",
    "createdAt": "2019-03-06T20:14:15.164Z",
    "createdBy": "sysadmin",
    "updatedAt": "2019-03-06T20:14:15.168Z",
    "updatedBy": "sysadmin",
    "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/projects/c6102d0c-9301-4c87-96ec-493fcf1c86f5",
    "message": "Project too-many-versions-5e6a5320-1105-4f6f-8d18-39cda054b248 has 21 versions which is greater than the recommend maximum of 20. There are 0 versions that have been released. There are 0 versions that have been archived.You should review these versions and remove extraneous ones, and their scans, to reclaim space and reduce clutter. Typically there should be one version per development branch, and one version per release. When new vulnerabilities are published you want to be able to quickly identify which projects are affected and take action. Keeping a large number of un-released versions in the system will make that difficult. And accruing a large number of versions per project can lead to serious performance degradation. Look at https://github.com/blackducksoftware/hub-rest-api-python/tree/master/examples for python examples for finding/deleting/removing versions and their scans"
  }
]
cat /var/log/sage_says.json | jq .unmapped_scans
{
  "message": "Unmapped scans represent scanning data that is not mapped to any project-version, and hence, they are potentially consuming space that should be reclaimed.",
  "scans": [
    {
      "name": "showcase/struts2-showcase/org.apache.struts/struts2-showcase/2.6-SNAPSHOT maven/bom",
      "createdAt": "2019-03-05T16:39:04.848Z",
      "scanSize": 0,
      "updatedAt": "2019-03-06T18:40:01.064Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/587cfd0d-2067-3d37-a1af-3526784ecc99"
    },
    {
      "name": "showcase/struts2-showcase/2.6-SNAPSHOT scan",
      "createdAt": "2019-03-05T16:29:54.048Z",
      "scanSize": 40474695,
      "updatedAt": "2019-03-06T18:40:00.929Z",
      "url": "https://ec2-18-217-189-8.us-east-2.compute.amazonaws.com/api/codelocations/51361d69-e10e-32de-b527-dc42376a6ef3"
    }
  ]
}
```

Output from Sage can form the input to other tools.

# Release History <a name=release-history />

## March 6, 2019

Adding more fine-grained analysis of projects

## March 3, 2019

Added job information





