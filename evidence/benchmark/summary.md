# FlashScope 2.3M Record Benchmark Evidence

## Benchmark Overview
- **Total Records Ingested**: 2,300,000
- **Throughput**: **63,239 records/sec**
- **Ingestion Time**: 36.37 s
- **Total Pipeline Runtime**: 36.76 s
- **Peak Memory (RSS)**: 141.75 MB
- **SQLite Database Size**: 914.7 MB
- **Fault Signatures Detected**: 31
- **Consolidated Incidents**: 91

## Pipeline Scalability Proof
- **Chunked Transactions**: SQLite WAL mode + 50,000-record batch commits prevented memory exhaustion.
- **Constant Memory Footprint**: Ingestion streaming maintained steady sub-GB RSS despite processing over 2.3 million records.
- **Relational Indexing**: B-tree indices on `(timestamp)`, `(signature_id)`, and `(run_id, case_id)` enable sub-second analytical queries.
