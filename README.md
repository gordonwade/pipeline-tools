# pipeline-tools

[![Build Status](https://travis-ci.org/HumanCellAtlas/pipeline-tools.svg?branch=master)](https://travis-ci.org/HumanCellAtlas/pipeline-tools)
[![Documentation Status](https://readthedocs.org/projects/pipeline-tools/badge/?version=latest)](http://pipeline-tools.readthedocs.io/en/latest/?badge=latest)


This repo contains Python code and pipelines for interacting with the Human Cell Atlas Data Coordination Platform. They are used by the Secondary Analysis Service.

The pipelines wrap analysis pipelines from the Skylab repo and provide some glue to interface with the DCP. The adapter pipelines take bundle ids as inputs, query the Data Storage Service to find the input files needed by the analysis pipelines, then run the analysis pipelines and submit the results to the Ingest Service. This helps us keep the analysis pipelines themselves free of dependencies on the DCP.

## Run tests

### Create a virtual environment

```
virtualenv pipeline-tools-test-env
source pipeline-tools-test-env/bin/activate
pip install -r test-requirements.txt
```

### Run unit tests

```
pytest -v
```
