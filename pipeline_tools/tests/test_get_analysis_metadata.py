import os
import pytest
import requests
from requests.auth import HTTPBasicAuth
from unittest.mock import patch

from pipeline_tools import get_analysis_metadata
from pipeline_tools.http_requests import HttpRequests
from pipeline_tools.tests.http_requests_manager import HttpRequestsManager


data_dir = os.path.split(__file__)[0] + '/data/'


@pytest.fixture(scope='module')
def test_data():
    class Data:
        workflow_id = 'id'
        base_url = 'https://cromwell.mint-environment.broadinstitute.org/api/workflows/v1'
        caas_base_url = 'https://cromwell.caas-dev.broadinstitute.org/api/workflows/v1'
        cromwell_metadata_url = '{}/{}/metadata?expandSubWorkflows=true'.format(base_url, workflow_id)
        caas_metadata_url = '{}/{}/metadata?expandSubWorkflows=true'.format(caas_base_url, workflow_id)
        cromwell_query_url = '{0}/query?id={1}&additionalQueryResultFields=labels'.format(base_url, workflow_id)
        caas_query_url = '{0}/query?id={1}&additionalQueryResultFields=labels'.format(caas_base_url, workflow_id)
        analysis_output_path = 'gs://broad-dsde-mint-dev-cromwell-execution/cromwell-executions' \
                               '/AdapterSmartSeq2SingleCell/adapter_workflow_id/call-analysis/SmartSeq2SingleCell' \
                               '/analysis_subworkflow_id/call-qc/RunHisat2Pipeline/qc_workflow_id/call-Hisat2' \
                               '/12345_qc.hisat2.met.txt'
        query_workflow_response_200 = {
            "results": [
                {
                    "name": "AdapterSmartSeq2SingleCell",
                    "id": "id",
                    "labels": {
                        "cromwell-workflow-id": "cromwell-id",
                        "workflow-version": "testing-fake-version",
                        "bundle-version": "foo-version",
                        "caas-collection-name": "dev-workflows",
                        "mintegration-test": "true",
                        "bundle-uuid": "foo-bundle",
                        "workflow-name": "AdapterSmartSeq2SingleCell"
                    },
                    "submission": "foo-submission-time",
                    "status": "Succeeded",
                    "end": "foo-submission-end_time",
                    "start": "foo-submission-start_time"
                }
            ],
            "totalResultsCount": 1
        }

    return Data


def mocked_get_auth():
    return HTTPBasicAuth('user', 'password')


def mocked_generate_auth_header_from_key_file(foo_credentials):
    return {'Authorization': 'bearer 12345'}


class TestGetAnalysisMetadata(object):

    def test_get_analysis_workflow_id(self, test_data, tmpdir):
        current_file_path = tmpdir.join('workflow_id.txt')
        analysis_output_path = test_data.analysis_output_path

        with tmpdir.as_cwd():  # this stops unittests from writing files and polluting the directory
            result = get_analysis_metadata.get_analysis_workflow_id(analysis_output_path)
        expected = 'analysis_subworkflow_id'
        assert result == expected
        assert current_file_path.read() == 'analysis_subworkflow_id'

    def test_get_adapter_workflow_id(self, test_data):
        analysis_output_path = test_data.analysis_output_path

        result = get_analysis_metadata.get_adapter_workflow_id(analysis_output_path)
        expected = 'adapter_workflow_id'
        assert result == expected

    def test_get_auth(self):
        credentials_file = '{0}test_credentials.txt'.format(data_dir)
        auth = get_analysis_metadata.get_auth(credentials_file)
        expected_auth = HTTPBasicAuth('fake-user', 'fake-password')
        assert auth == expected_auth

    def test_get_adapter_workflow_version_success(self, requests_mock, test_data, tmpdir):
        current_file_path = tmpdir.join('pipeline_version.txt')

        def _request_callback(request, context):
            context.status_code = 200
            return test_data.query_workflow_response_200

        requests_mock.get(test_data.cromwell_query_url, json=_request_callback)
        with patch('pipeline_tools.get_analysis_metadata.get_auth', side_effect=mocked_get_auth), \
             tmpdir.as_cwd(), \
             HttpRequestsManager():
            get_analysis_metadata.get_adapter_workflow_version(test_data.base_url,
                                                               test_data.workflow_id,
                                                               HttpRequests(),
                                                               use_caas=False)
            assert requests_mock.call_count == 1
            assert current_file_path.read() == 'testing-fake-version'

    def test_get_adapter_workflow_version_using_caas(self, requests_mock, test_data, tmpdir):
        current_file_path = tmpdir.join('pipeline_version.txt')

        def _request_callback(request, context):
            context.status_code = 200
            return test_data.query_workflow_response_200

        requests_mock.get(test_data.caas_query_url, json=_request_callback)
        with patch('pipeline_tools.get_analysis_metadata.cromwell_tools.generate_auth_header_from_key_file',
                   side_effect=mocked_generate_auth_header_from_key_file), tmpdir.as_cwd(), HttpRequestsManager():
            get_analysis_metadata.get_adapter_workflow_version(test_data.caas_base_url,
                                                               test_data.workflow_id,
                                                               HttpRequests(),
                                                               use_caas=True)
        assert requests_mock.call_count == 1
        assert current_file_path.read() == 'testing-fake-version'

    def test_get_adapter_workflow_version_retries_on_failure(self, requests_mock, test_data):
        def _request_callback(request, context):
            context.status_code = 500
            return {'status': 'error', 'message': 'Internal Server Error'}

        requests_mock.get(test_data.cromwell_query_url, json=_request_callback)
        with patch('pipeline_tools.get_analysis_metadata.get_auth', side_effect=mocked_get_auth), \
             pytest.raises(requests.HTTPError), HttpRequestsManager():
            get_analysis_metadata.get_adapter_workflow_version(test_data.base_url,
                                                               test_data.workflow_id,
                                                               HttpRequests(),
                                                               use_caas=False)
        assert requests_mock.call_count == 3

    def test_get_metadata_success(self, requests_mock, test_data, tmpdir):
        current_file_path = tmpdir.join('metadata.json')

        def _request_callback(request, context):
            context.status_code = 200
            return {
                'workflowName': 'TestWorkflow'
            }

        requests_mock.get(test_data.cromwell_metadata_url, json=_request_callback)
        with patch('pipeline_tools.get_analysis_metadata.get_auth', side_effect=mocked_get_auth), \
             tmpdir.as_cwd(), \
             HttpRequestsManager():
            get_analysis_metadata.get_metadata(test_data.base_url,
                                               test_data.workflow_id,
                                               HttpRequests(),
                                               use_caas=False)
        assert requests_mock.call_count == 1
        assert current_file_path.read() is not None

    def test_get_metadata_using_caas(self, requests_mock, test_data, tmpdir):
        current_file_path = tmpdir.join('metadata.json')

        def _request_callback(request, context):
            context.status_code = 200
            return {
                'workflowName': 'TestWorkflow'
            }

        requests_mock.get(test_data.caas_metadata_url, json=_request_callback)
        with patch('pipeline_tools.get_analysis_metadata.cromwell_tools.generate_auth_header_from_key_file',
                   side_effect=mocked_generate_auth_header_from_key_file), tmpdir.as_cwd(), HttpRequestsManager():
            get_analysis_metadata.get_metadata(test_data.caas_base_url,
                                               test_data.workflow_id,
                                               HttpRequests(),
                                               use_caas=True)
        assert requests_mock.call_count == 1
        assert current_file_path.read() is not None

    def test_get_metadata_retries_on_failure(self, requests_mock, test_data):
        def _request_callback(request, context):
            context.status_code = 500
            return {'status': 'error', 'message': 'Internal Server Error'}

        requests_mock.get(test_data.cromwell_metadata_url, json=_request_callback)
        with patch('pipeline_tools.get_analysis_metadata.get_auth', side_effect=mocked_get_auth), \
             pytest.raises(requests.HTTPError), HttpRequestsManager():
            get_analysis_metadata.get_metadata(test_data.base_url,
                                               test_data.workflow_id,
                                               HttpRequests(),
                                               use_caas=False)
        assert requests_mock.call_count == 3
