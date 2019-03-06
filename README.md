# Project Sage

Analyze usage of a Black Duck system and offer sage advice for how to improve that usage to get the most value out of the product. Identifies issues which represent poor practices and/or areas where best practices could/should be applied.

## Table Of Contents

- [Goals](#goals)
- [How to Run and Get Results](#run)
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

Sage uses:

- Python3
- An API token from your Black Duck server
  - The user account this token is issued from needs to have visibility to all the projects, versions, and scans you want to analyze, e.g. has role 'Systemadmin', 'Super User', or 'Global Code Scanner'
- Highly recommended: [virtualenv](https://virtualenv.pypa.io/en/latest/), [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)

To run,

```bash
mkvirtualenv sage # optional, but again, nice to use virtualenv and virtualenvwrapper
pip install -r requirements.txt
python3 sage.py -h # for help
python3 sage.py https://your-hub-dns {api-token}
```

# Release History <a name=release-history />

## Mar 3, 2019

Added job information





