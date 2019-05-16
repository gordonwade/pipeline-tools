from pipeline_tools.shared import metadata_utils
from pipeline_tools.shared import tenx_utils
from pipeline_tools.shared.http_requests import HttpRequests


def create_optimus_drop_seq_input_tsv(uuid, version, dss_url, input_tsv_name='inputs.csv'):
    """Create TSV of Optimus Drop Seq inputs

    Args:
        uuid (str): the bundle uuid
        version (str): the bundle version
        dss_url (str): the DCP Data Storage Service
        input_tsv_name (str): The file name of the input TSV(CSV) file. By default, it's set to 'inputs.tsv',
                              which will be consumed by the pipelines.

    Returns:
        None: this function will write the TSV(CSV) file of cloud paths for the input files.
    """
    # Get bundle manifest
    print('Getting bundle manifest for id {0}, version {1}'.format(uuid, version))
    primary_bundle = metadata_utils.get_bundle_metadata(
        uuid=uuid, version=version, dss_url=dss_url, http_requests=HttpRequests()
    )

    # Parse inputs from metadata
    print('Gathering 2 fastq inputs')
    fastq_1_url = fastq_2_url = None
    sequence_files = primary_bundle.sequencing_output

    for sf in sequence_files:
        if fastq_1_url and fastq_2_url:
            return fastq_1_url, fastq_2_url  # early termination
        if sf.read_index == 'read1':
            fastq_1_url = sf.manifest_entry.url
        if sf.read_index == 'read2':
            fastq_2_url = sf.manifest_entry.url

    # fastq_1_url = ["gs://hca-dcp-mint-test-data/20190507-PipelinesSurge/Drop-Seq/Retinal-Bipolar-Neuron/Bipolar4_900K_R1.fastq.gz"]
    # fastq_2_url = ["gs://hca-dcp-mint-test-data/20190507-PipelinesSurge/Drop-Seq/Retinal-Bipolar-Neuron/Bipolar4_900K_R2.fastq.gz"]

    sample_id = metadata_utils.get_sample_id(primary_bundle)

    print('Creating input map')
    with open(input_tsv_name, 'w') as f:
        # DropSeq pipeline expects a CSV rather than a TSV
        f.write('{0}, {1}, {2}\n'.format(sample_id, fastq_1_url, fastq_2_url))
    print('Wrote input map to disk.')
