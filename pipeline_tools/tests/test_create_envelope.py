import unittest
import os
import json
import pipeline_tools.create_envelope as submit


class TestCreateEnvelope(unittest.TestCase):

    def test_get_entity(self):
        with open(self.data_file('response.json')) as f:
            js = json.load(f)
            entity_url = submit.get_entity_url(js, 'analyses')
            self.assertEqual(entity_url, 'http://api.ingest.dev.data.humancellatlas.org/analyses')

    def test_get_input_bundle_uuid(self):
        with open(self.data_file('analysis.json')) as f:
            js = json.load(f)
            self.assertEqual(submit.get_input_bundle_uuid(js), '75a7f618-9adc-48af-a249-0010305160f6')

    def test_get_output_files(self):
        schema_version = 'version_232'
        analysis_file_schema_url = 'https://schema.humancellatlas.org/type/file/{}/analysis_file'.format(schema_version)
        file_core_schema_url = 'https://schema.humancellatlas.org/core/file/{}/file_core'.format(schema_version)

        with open(self.data_file('analysis.json')) as f:
            js = json.load(f)
            outputs = submit.get_output_files(js, schema_version)
            self.assertEqual(len(outputs), 3)
            self.assertEqual(outputs[0]['fileName'], 'aligned_bam')
            self.assertEqual(outputs[0]['content']['schema_type'], 'file')
            self.assertEqual(outputs[0]['content']['describedBy'], analysis_file_schema_url)
            self.assertEqual(outputs[0]['content']['file_core']['describedBy'], file_core_schema_url)
            self.assertEqual(outputs[0]['content']['file_core']['file_name'], 'aligned_bam')
            self.assertEqual(outputs[0]['content']['file_core']['file_format'], 'bam')

    def test_check_status_bad_codes(self):
        with self.assertRaises(ValueError):
            submit.check_status(404, 'foo')
        with self.assertRaises(ValueError):
            submit.check_status(500, 'foo')
        with self.assertRaises(ValueError):
            submit.check_status(301, 'foo')

    def test_check_status_acceptable_codes(self):
        try:
          submit.check_status(200, 'foo')
        except ValueError as e:
            self.fail(str(e))

        try:
            submit.check_status(202, 'foo')
        except ValueError as e:
            self.fail(str(e))

        try:
            submit.check_status(301, 'foo', '3xx')
        except ValueError as e:
            self.fail(str(e))

    def data_file(self, file_name):
        return os.path.split(__file__)[0] + '/data/'  + file_name

if __name__ == '__main__':
    unittest.main()
