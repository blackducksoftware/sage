from datetime import timedelta
from django.test import TestCase

from bd_sage_app.models import Job
from sage import sageApi

class SageAPITest(TestCase):
    #
    # Get project list
    #
    def test_get_project_list(self):
        project_list = sageApi._get_project_list(project_list="project1,project2")
        self.assertEqual(project_list, ['project1', 'project2'])

    def test_get_project_list_does_not_respond_to_other_kwargs(self):
        project_list = sageApi._get_project_list(not_project_list="project1,project2")
        self.assertEqual(project_list, [])

    def test_get_project_list_returns_all_for_empty_project_list(self):
        project_list = sageApi._get_project_list(project_list="")
        self.assertEqual(project_list, [])

    #
    # Get version phases
    #
    def test_get_project_version_phases(self):
        phases_list = sageApi._get_project_version_phases(phases="in-development,in-planning")
        self.assertEqual(phases_list, ['DEVELOPMENT', 'PLANNING'])

    def test_get_project_version_phases_does_not_respond_to_other_kwargs(self):
        phases_list = sageApi._get_project_version_phases(not_phases_list="in-development,in-planning")
        self.assertEqual(phases_list, ['DEVELOPMENT'])

    def test_get_project_version_phases_returns_default_for_empty_phases_list(self):
        phases_list = sageApi._get_project_version_phases(phases="")
        self.assertEqual(phases_list, ['DEVELOPMENT'])

    #
    # Get job info
    #
    def test_get_job_info_defaults(self):
        job = Job()
        job.job_name = "my_job"

        job_from_sage, job_name, test_mode  = sageApi._get_job_info(job=job)
        self.assertEqual(job_from_sage, job)
        self.assertEqual(job_name, "my_job")
        self.assertEqual(test_mode, True)

    def test_get_job_info_disabling_test_mode(self):
        job = Job()
        job.job_name = "my_job"
        job.test_mode = False

        job_from_sage, job_name, test_mode  = sageApi._get_job_info(job=job)
        self.assertEqual(job_from_sage, job)
        self.assertEqual(job_name, "my_job")
        self.assertEqual(test_mode, False)

    def test_get_job_info_when_no_job_is_supplied(self):
        job, job_name, test_mode = sageApi._get_job_info()
        self.assertEqual(job, None)
        self.assertEqual(job_name, "Unknown")
        self.assertEqual(test_mode, True)


    #
    # Get older than
    #
    def test_get_older_than1(self):
        older_than = sageApi._get_older_than(older_than="360d")
        self.assertEqual(older_than, timedelta(days=360))

    def test_get_older_than2(self):
        older_than = sageApi._get_older_than(older_than="2w3d")
        self.assertEqual(older_than, timedelta(days=(14+3)))

    def test_get_older_than_default1(self):
        older_than = sageApi._get_older_than()
        self.assertEqual(older_than, timedelta(days=180))

    def test_get_older_than_default2(self):
        older_than = sageApi._get_older_than(older_than="")
        self.assertEqual(older_than, timedelta(days=180))


    #
    # Get keep only X versions
    #
    def test_get_keep_only_default(self):
        keep_only = sageApi._get_keep_only()
        self.assertEqual(keep_only, 20)

    def test_get_keep_only(self):
        keep_only = sageApi._get_keep_only(keep_only=30)
        self.assertEqual(keep_only, 30)

    #
    # Delete empty versions
    #
    def test_delete_empty_versions1(self):
        pass


