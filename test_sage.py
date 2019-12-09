import json
import pytest

from unittest.mock import MagicMock

from blackduck.HubRestApi import HubInstance
from sage import BlackDuckSage

fake_hub_host = "https://my-hub-host"
fake_bearer_token = "aFakeToken"
invalid_bearer_token="anInvalidTokenValue"
invalid_csrf_token="anInvalidCSRFTokenValue"
made_up_api_token="theMadeUpAPIToken"
hub_version = '2019.10.1'

@pytest.fixture()
def mock_hub_instance(requests_mock):
    requests_mock.post(
        "https://my-hub-host/api/tokens/authenticate", 
        content = json.dumps({'bearerToken': invalid_bearer_token}).encode('utf-8'),
        headers={
                'X-CSRF-TOKEN': invalid_csrf_token, 
                'Content-Type': 'application/json'
            }
    )
    requests_mock.get(
        "{}/api/current-version".format(fake_hub_host),
        json = {
            "version": hub_version,
            "_meta": {
                "allow": [
                    "GET"
                ],
                "href": "{}/api/current-version".format(fake_hub_host)
            }
        }
    )

    yield HubInstance(fake_hub_host, api_token=made_up_api_token)


def test_construction(mock_hub_instance):
    sage = BlackDuckSage(mock_hub_instance, file="sage_says.json")

    assert 'version' in sage.hub.version_info
    assert sage.hub.version_info['version'] == hub_version
    assert sage.file == "sage_says.json"
    assert sage.max_versions_per_project == 20
    assert sage.max_scans_per_version == 10
    assert sage.max_age_for_unmapped_scans == 365
    assert sage.min_time_between_versions == 1
    assert sage.min_ratio_of_released_versions == 0.1
    assert sage.max_recommended_projects == 1000
    assert sage.max_time_to_retrieve_projects == 60

    with pytest.raises(Exception) as e_info:
        class NotAHubInstance:
            pass
        not_a_hub_instance = NotAHubInstance()
        sage = BlackDuckSage(not_a_hub_instance)

def test_get_data(mock_hub_instance):
    sage = BlackDuckSage(mock_hub_instance, file="sage_says.json")

    num_projects = 10
    get_projects_return = { 
        'items': [{'name': 'project{}'.format(i), '_meta': {'href': 'proj_url_{}'.format(i)}} for i in range(num_projects)]
    }
    sage.hub.get_projects = MagicMock(return_value=get_projects_return)

    num_versions_per_project = 10
    get_project_versions_return = { 
        'items': [{'versionName': '{}.0'.format(i), '_meta': {'href': 'v_url_{}'.format(i)}} for i in range(num_versions_per_project)]
    }
    sage.hub.get_project_versions = MagicMock(return_value=get_project_versions_return)
    
    num_scans_per_version = 3
    get_version_codelocations_return = { 
        'items': [{'name': 'scan{}'.format(i), '_meta': {'href': 's_url_{}'.format(i)}} for i in range(num_scans_per_version)]
    }
    sage.hub.get_version_codelocations = MagicMock(return_value=get_version_codelocations_return)
    
    num_policies = 5
    get_policies_return = { 
        'items': [{'name': 'policy_{}'.format(i), '_meta': {'href': 'policy_url_{}'.format(i)}} for i in range(num_policies)]
    }
    sage.hub.get_policies = MagicMock(return_value=get_policies_return)
    
    total_num_scans = 100
    get_codelocations_return = { 
        'items': [{'name': 'scan{}'.format(i), '_meta': {'href': 's_url_{}'.format(i)}} for i in range(total_num_scans)]
    }
    sage.hub.get_codelocations = MagicMock(return_value=get_codelocations_return)
    
    sage.data = {}
    sage._get_data()

    sage.hub.get_projects.assert_called_once_with(limit=99999)
    assert len(sage.data['projects']) == num_projects
    assert sage.hub.get_project_versions.call_count == num_projects
    assert sage.hub.get_version_codelocations.call_count == num_projects * num_versions_per_project
    sage.hub.get_policies.assert_called_once_with(parameters={'limit':1000})
    sage.hub.get_codelocations.assert_called_once_with(limit=99999)
    assert sage.data['total_projects'] == num_projects
    assert sage.data['total_versions'] == num_projects * num_versions_per_project
    assert sage.data['total_scans'] == total_num_scans
    assert sage.data['scans'] == get_codelocations_return['items']


def test_find_versions_with_zero_scans(mock_hub_instance):
    sage = BlackDuckSage(mock_hub_instance, file="sage_says.json")

    sage.data = {
        'projects': [
            {
                'name': 'project1',
                'versions': [
                    {
                        'versionName': '1.0',
                        'num_scans': 0
                    },
                    {
                        'versionName': '2.0',
                        'num_scans': 1
                    },
                ]
            },
            {
                'name': 'project2',
                'versions': [
                    {
                        'versionName': '1.0',
                        'num_scans': 0
                    },
                    {
                        'versionName': '2.0',
                        'num_scans': 1
                    },
                ]
            },
        ]
    }
    sage._find_versions_with_zero_scans()
    assert len(sage.data['versions_with_zero_scans']) == 2
    for v in sage.data['versions_with_zero_scans']:
        assert v['num_scans'] == 0
        assert 'versionName' in v
        assert v['versionName'] == "1.0"

def test_find_versions_with_too_many_scans(mock_hub_instance):
    sage = BlackDuckSage(mock_hub_instance, file="sage_says.json")

    sage.data = {
        'projects': [
            {
                'name': 'project1',
                'versions': [
                    {
                        'versionName': '1.0',
                        'num_scans': 0
                    },
                    {
                        'versionName': '2.0',
                        'num_scans': 21
                    },
                ]
            },
            {
                'name': 'project2',
                'versions': [
                    {
                        'versionName': '1.0',
                        'num_scans': 0
                    },
                    {
                        'versionName': '2.0',
                        'num_scans': 21
                    },
                ]
            },
            {
                'name': 'project3',
                'versions': [
                    {
                        'versionName': '1.0',
                        'num_scans': 0
                    },
                    {
                        'versionName': '2.0',
                        'num_scans': 21
                    },
                ]
            },
        ]
    }
    sage._find_versions_with_too_many_scans()
    assert len(sage.data['versions_with_too_many_scans']) == 3
    for v in sage.data['versions_with_too_many_scans']:
        assert v['num_scans'] == 21
        assert 'versionName' in v
        assert v['versionName'] == "2.0"

def test_find_projects_with_too_many_versions(mock_hub_instance):
    sage = BlackDuckSage(mock_hub_instance, file="sage_says.json")

    sage.data = {
        'projects': [
            {
                'name': 'projects_with_too_many_versions',
            },
            {
                'name': 'project2',
            },
        ]
    }
    sage.data['projects'][0]['versions'] = [{'versionName': i, 'num_scans': 2} for i in range(21)]
    sage.data['projects'][1]['versions'] = [{'versionName': i, 'num_scans': 2} for i in range(2)]
    for p in sage.data['projects']:
        p['num_versions'] = len(p['versions'])
    sage._find_projects_with_too_many_versions()
    assert len(sage.data['projects_with_too_many_versions']) == 1
    for p in sage.data['projects_with_too_many_versions']:
        assert p['name'] == 'projects_with_too_many_versions'
        assert p['num_versions'] == 21





