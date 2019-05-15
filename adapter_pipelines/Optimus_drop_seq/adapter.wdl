import "OptimusDropSeq.wdl" as OptimusDropSeq
import "submit.wdl" as submit_wdl


task GetInputs {
  String bundle_uuid
  String bundle_version
  String dss_url
  Int? retry_timeout
  Float? retry_multiplier
  Int? retry_max_interval
  Int? individual_request_timeout
  Boolean record_http
  String pipeline_tools_version

  command <<<
    export RECORD_HTTP_REQUESTS="${record_http}"
    export RETRY_TIMEOUT="${retry_timeout}"
    export RETRY_MULTIPLIER="${retry_multiplier}"
    export RETRY_MAX_INTERVAL="${retry_max_interval}"
    export INDIVIDUAL_REQUEST_TIMEOUT="${individual_request_timeout}"

    # Force the binary layer of the stdout and stderr streams to be unbuffered.
    python -u <<CODE
    from pipeline_tools.pipelines.optimus_drop_seq import optimus_drop_seq

    optimus.create_optimus_drop_seq_input_tsv(
                "${bundle_uuid}",
                "${bundle_version}",
                "${dss_url}")

    CODE
  >>>
  runtime {
    docker: "quay.io/humancellatlas/secondary-analysis-pipeline-tools:" + pipeline_tools_version
  }
  output {
    String sample_id = read_string("sample_id.txt")
    Array[String] r1_fastq = read_lines("r1.txt")
    Array[String] r2_fastq = read_lines("r2.txt")
    Array[File] http_requests = glob("request_*.txt")
    Array[File] http_responses = glob("response_*.txt")
  }
}


workflow AdapterOptimusDropSeq {
  String bundle_uuid
  String bundle_version

  File tar_star_reference  # star reference
  File annotations_gtf  # gtf containing annotations for gene tagging
  File ref_genome_fasta  # genome fasta file
  String fastq_suffix = ".gz"  # add this suffix to fastq files for picard
  
  # Note: This "None" is a workaround in WDL-draft to simulate a "None" type
  # once the official "None" type is introduced (probably in WDL 2.0)
  # we should consider replace this dummy None with the built-in None!
  # 
  # Also, to properly use this dummy None, we should avoid passing in any
  # inputs that could possibly override this
  Array[File]? None

  # Submission
  File format_map
  String dss_url
  String submit_url
  String method
  String schema_url
  String cromwell_url
  String analysis_process_schema_version
  String analysis_protocol_schema_version
  String analysis_file_version
  String run_type
  Int? retry_max_interval
  Float? retry_multiplier
  Int? retry_timeout
  Int? individual_request_timeout
  String reference_bundle

  # Set runtime environment such as "dev" or "staging" or "prod" so submit task could choose proper docker image to use
  String runtime_environment
  # By default, don't record http requests, unless we override in inputs json
  Boolean record_http = false
  Int max_cromwell_retries = 0
  Boolean add_md5s = false

  String pipeline_tools_version = "kmk-drop-seq-adapter"

  call GetInputs as prep {
    input:
      bundle_uuid = bundle_uuid,
      bundle_version = bundle_version,
      dss_url = dss_url,
      retry_multiplier = retry_multiplier,
      retry_max_interval = retry_max_interval,
      retry_timeout = retry_timeout,
      individual_request_timeout = individual_request_timeout,
      record_http = record_http,
      pipeline_tools_version = pipeline_tools_version
  }

  call OptimusDropSeq.OptimusDropSeq as analysis {
    input:
      r1_fastq = prep.r1_fastq,
      r2_fastq = prep.r2_fastq,
      i1_fastq = if (length(prep.i1_fastq) <= 0) then None else prep.i1_fastq,
      sample_id = prep.sample_id,
      tar_star_reference = tar_star_reference,
      annotations_gtf = annotations_gtf,
      ref_genome_fasta = ref_genome_fasta,
      fastq_suffix = fastq_suffix
  }

  # placeholder here
  Array[Object] inputs = []
  Array[Object] outputs = []

  call submit_wdl.submit {
    input:
      inputs = inputs,
      outputs = outputs,
      format_map = format_map,
      submit_url = submit_url,
      cromwell_url = cromwell_url,
      input_bundle_uuid = bundle_uuid,
      reference_bundle = reference_bundle,
      run_type = run_type,
      schema_url = schema_url,
      analysis_process_schema_version = analysis_process_schema_version,
      analysis_protocol_schema_version = analysis_protocol_schema_version,
      analysis_file_version = analysis_file_version,
      method = method,
      retry_multiplier = retry_multiplier,
      retry_max_interval = retry_max_interval,
      retry_timeout = retry_timeout,
      individual_request_timeout = individual_request_timeout,
      runtime_environment = runtime_environment,
      record_http = record_http,
      pipeline_tools_version = pipeline_tools_version,
      add_md5s = add_md5s,
      pipeline_version = analysis.pipeline_version,
      # The disk space value here is still an experiment value, need to 
      # be optimized based on historical data by CBs
      disk_space = ceil(size(analysis.bam, "GB") * 2 + 50)
  }
}
