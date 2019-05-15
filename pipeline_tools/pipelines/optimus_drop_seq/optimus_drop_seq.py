from pipeline_tools.shared import metadata_utils
from pipeline_tools.shared import tenx_utils
from pipeline_tools.shared.http_requests import HttpRequests


def create_optimus_drop_seq_input_tsv(uuid, version, dss_url):
    """Create TSV of Optimus Drop Seq inputs

    Args:
        uuid (str): the bundle uuid
        version (str): the bundle version
        dss_url (str): the DCP Data Storage Service

    Returns:
        TSV of input file cloud paths
    """

    # hard-coding here, later we add logic to extract the information from bundle.
    r1_urls = ["gs://hca-dcp-mint-test-data/20190507-PipelinesSurge/Drop-Seq/Retinal-Bipolar-Neuron/Bipolar4_900K_R1.fastq.gz"]
    r2_urls = ["gs://hca-dcp-mint-test-data/20190507-PipelinesSurge/Drop-Seq/Retinal-Bipolar-Neuron/Bipolar4_900K_R2.fastq.gz"]

    print('Writing r1.txt and r2.txt')
    with open('r1.txt', 'w') as f:
        for url in r1_urls:
            f.write(url + '\n')
    with open('r2.txt', 'w') as f:
        for url in r2_urls:
            f.write(url + '\n')

    # hard-coding here, later we add logic to extract the information from bundle.
    sample_id = "Bipolar4_sample"
    print('Writing sample ID to sample_id.txt')
    with open('sample_id.txt', 'w') as f:
        f.write('{0}'.format(sample_id))

    print('Finished writing files')
