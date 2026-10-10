# Assessment test fixtures

Small fixtures for the `bioheaders assess` tests (`tests/assess_*_test.py`).

Files named after a provider (for example `ncbi-refseq_gff3_...`) are copied
unchanged from the FHR-Specification shared fixtures in `assessment/headers/`,
`assessment/pairs/` and `assessment/edge/`. Their provenance (source URL, release
and fetch date) is recorded in FHR-Specification `assessment/manifest.json`. They
hold real header lines only; any record lines are minimal and synthetic. Other
files here are synthetic unit cases written for these tests.

Licensed MPL-2.0, like the rest of this repository. Provider header lines are
short factual metadata from public download files.
