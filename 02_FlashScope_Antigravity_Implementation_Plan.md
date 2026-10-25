# FlashScope — AI-Agent Implementation Plan

## 1. Project Mission

Build **FlashScope** as an SSD telemetry normalization, log-correlation, regression-analysis, and failure-triage pipeline.

This project is based on the resume claim:

> FlashScope – SSD telemetry, log-correlation, and failure-triage pipeline (Python, pandas, SQLite, Plotly, regex)

Primary priorities:

1. **Substantiate the resume's telemetry/triage claims.**
2. **Build a robust evidence-linked failure-analysis pipeline.**
3. **Generate interview-ready diagnosis scenarios.**
4. **Create a comparison dashboard as the final viewing layer.**

FlashScope should ingest both real artifacts produced by QualiDrive and synthetic fault records so that the project can be fully developed without physical NVMe hardware.

---

# 2. Resume Claims This Project Must Support

Implementation must cover:

- normalize fio output
- normalize NVMe error entries
- normalize SMART counters
- normalize PCIe events
- normalize kernel logs
- common schema keyed by:
  - device
  - firmware
  - workload
  - test phase
  - timestamp
- signature rules for:
  - media errors
  - controller resets
  - timeouts
  - thermal throttling
  - latency regressions
  - unsafe-shutdown deltas
- duplicate-failure grouping
- evidence linkage
- processing at least 2.3M generated + captured log records
- firmware-to-firmware regression comparison
- first-failure timeline visualization
- triage automation

Historical percentage improvements on the resume must not be fabricated. Recreated benchmark measurements must be stored separately.

---

# 3. Data Sources

Use three sources.

## 3.1 QualiDrive artifacts

Import:

```text
fio JSON / JSON+
NVMe identify data
SMART/health snapshots
NVMe error logs
dmesg
journalctl
PCIe/sysfs snapshots
case metadata
```

This is the highest-quality source because it connects two projects.

---

# 4. Synthetic Failure Corpus

Build a generator capable of producing millions of timestamped records.

Required fault families:

```text
MEDIA_ERROR
CONTROLLER_RESET
IO_TIMEOUT
THERMAL_THROTTLE
LATENCY_REGRESSION
UNSAFE_SHUTDOWN_DELTA
PCIE_LINK_DOWNGRADE
FIRMWARE_ASSERT
QUEUE_STALL
DEVICE_DISAPPEAR
```

Generate clean and faulty runs.

Data must contain enough noise to force real correlation.

Example:

```text
normal fio samples
normal kernel chatter
temperature changes
unrelated PCIe lines
background service logs
fault signal
post-fault recovery logs
```

---

# 5. Captured Fixture Corpus

Check in small anonymized/generated fixtures representing:

```text
nvme log smart
nvme log error
dmesg
journalctl
fio JSON+
lspci
iostat
```

Do not use proprietary logs.

Do not claim synthetic faults are real vendor failures.

---

# 6. 2.3 Million Record Requirement

Create:

```bash
make generate-corpus RECORDS=2300000
```

The output may be compressed JSONL/CSV/Parquet.

The agent must prove:

```text
input records >= 2,300,000
normalized records
processing runtime
peak memory
rule-match counts
```

The 2.3M figure is practical to reproduce and should be verified in evidence.

---

# 7. Repository Structure

```text
flashscope/
├── README.md
├── PROJECT_CONSTITUTION.md
├── Makefile
├── pyproject.toml
├── .agents/
│   ├── rules/
│   ├── skills/
│   └── agents/
├── flashscope/
│   ├── ingest/
│   ├── parsers/
│   ├── normalize/
│   ├── correlate/
│   ├── signatures/
│   ├── grouping/
│   ├── regression/
│   ├── storage/
│   └── evidence/
├── fixtures/
├── generators/
├── sql/
├── tests/
├── benchmarks/
├── evidence/
├── dashboard/
├── infra/
└── interview/
```

---

# 8. Technology Stack

Core:

```text
Python 3.11+
pandas
SQLite
Plotly
regex
Pytest
Pydantic/dataclasses
```

Recommended for 2.3M scale:

```text
Parquet
PyArrow
DuckDB optional for benchmark comparison
```

The resume specifically names SQLite, so SQLite must remain part of the primary implementation.

Do not replace SQLite entirely with another database.

---

# 9. First Vertical Slice

Before generating millions of records:

```text
one QualiDrive run
      |
      v
ingest fio + SMART + dmesg
      |
      v
normalize into common schema
      |
      v
run signature rules
      |
      v
build incident
      |
      v
link raw evidence
      |
      v
show timeline
```

Only after this works should the agent scale to millions of records.

---

# 10. Common Event Schema

Use one normalized model.

Example:

```text
event_id
run_id
case_id
timestamp
source
device_id
controller_id
namespace_id
firmware
workload_id
test_phase
severity
event_type
metric_name
metric_value
unit
message
signature_id
raw_artifact
raw_offset
```

Raw source is always preserved.

Never discard source fidelity after parsing.

---

# 11. Parsers

Implement separate parser modules.

Required:

```text
fio JSON parser
fio JSON+ latency parser
NVMe SMART parser
NVMe error-log parser
dmesg parser
journalctl parser
lspci/sysfs parser
iostat parser
QualiDrive case-result parser
```

Each parser must have fixture-driven tests.

Test malformed input and version variation.

---

# 12. NVMe CLI Compatibility

Current `nvme-cli` releases have reorganized many older command names.

The project should normalize output rather than tie parsers to one exact command spelling.

Store:

```text
tool_name
tool_version
command
raw_output
```

with every captured artifact.

---

# 13. Normalization

Convert heterogeneous sources into stable values.

Examples:

```text
temperature -> Celsius
latency -> microseconds
bandwidth -> MiB/s
timestamps -> UTC
PCIe speed -> numeric GT/s
queue depth -> integer
```

Preserve original values.

Do not silently infer missing units.

---

# 14. Correlation Keys

Primary correlation:

```text
run_id
case_id
device_id
firmware
workload
timestamp
```

Time-window correlation must be configurable.

Example:

```text
controller reset at T0
fio latency spike within T0 ± 5 sec
kernel I/O timeout within T0 ± 5 sec
SMART error delta after T0
```

The incident links all evidence.

---

# 15. Signature Rule Engine

Rules should live in YAML where possible.

Example:

```yaml
id: controller_reset
severity: critical
sources:
  - dmesg
patterns:
  - "reset controller"
  - "controller is down"
correlation_window_seconds: 10
```

Rules may combine:

- regex
- numeric threshold
- counter delta
- sequence
- time correlation

---

# 16. Required Signature Families

## Media Error

Evidence candidates:

```text
NVMe media/data integrity count increases
NVMe error log
kernel I/O error
fio verify/error
```

## Controller Reset

```text
dmesg reset message
I/O pause
latency spike
optional PCIe event
```

## Timeout

```text
kernel timeout
fio stall
command-duration anomaly
```

## Thermal Throttling

```text
temperature rise
throughput reduction
device thermal status if exposed
recovery after cooling
```

Do not infer throttling solely from temperature.

Require a rule/evidence combination.

## Latency Regression

Compare same workload across baseline and candidate firmware.

Use:

```text
p50
p95
p99
p99.9
```

## Unsafe Shutdown Delta

Compare pre/post SMART values.

---

# 17. Duplicate Failure Grouping

Group repeated events into incidents.

Example:

```text
50 repeated kernel timeout lines
+
20 fio high-latency samples
+
1 controller reset
```

should not necessarily become 71 unrelated failures.

Create incident fingerprint:

```text
signature family
device
firmware
workload
time bucket
key normalized message tokens
```

Preserve occurrence count.

---

# 18. Evidence Graph

For every incident:

```text
Incident
  |
  +-- triggering signature
  +-- raw dmesg lines
  +-- SMART before
  +-- SMART after
  +-- fio interval
  +-- PCIe state
  +-- test manifest
```

Every incident must be auditable back to raw data.

---

# 19. First-Failure Timeline

Generate a timeline:

```text
T-30s normal I/O
T-5s latency p99 rises
T0 controller reset
T+1s kernel timeout
T+4s fio throughput collapses
T+11s device recovers
T+20s SMART error count changes
```

The timeline is one of the key outputs.

---

# 20. Firmware Regression Comparison

Compare:

```text
firmware A
firmware B
```

for identical workload fingerprints.

Metrics:

```text
IOPS
bandwidth
p50
p95
p99
p99.9
temperature
error count
timeout count
reset count
incident count
```

Flag regression when configured threshold is exceeded.

Do not compare unmatched workloads.

---

# 21. Root-Cause Assistance

FlashScope should aid triage, not pretend to prove silicon root cause.

Output:

```text
classification
confidence/rule strength
supporting evidence
contradictory evidence
next checks
```

Avoid overclaiming:

```text
"likely host-side timeout sequence"
```

is better than:

```text
"controller firmware bug proven"
```

unless evidence truly establishes it.

---

# 22. SQLite Schema

Tables:

```text
runs
devices
workloads
events
metrics
incidents
incident_evidence
artifacts
firmware_comparisons
```

Indexes:

```text
(timestamp)
(run_id, case_id)
(device_id, firmware)
(signature_id)
(event_type)
```

Benchmark ingestion/query behavior.

---

# 23. Scale Strategy

2.3M records must be processed reliably.

Use:

```text
chunked pandas ingestion
batch SQLite inserts
transactions
prepared statements
indexes created at appropriate phase
optional Parquet staging
```

Measure:

```text
records/sec
total runtime
peak RSS
SQLite size
incident count
```

Do not load everything into memory if unnecessary.

---

# 24. Performance Benchmark

Command:

```bash
make benchmark RECORDS=2300000
```

Output:

```text
evidence/benchmark/
environment.json
ingest.json
normalization.json
correlation.json
memory.json
summary.md
```

Historical resume claims should be documented separately from reproduction metrics.

---

# 25. Triage-Time Experiment

If attempting to recreate the "manual triage time reduction" concept:

1. Define 20-50 seeded incident cases.
2. Create a manual evidence checklist.
3. Record the time needed to locate relevant evidence manually on a small representative sample.
4. Compare with automatic incident output.
5. Document methodology.

Do not invent a 72% figure.

If no reliable human baseline is available, report automation coverage instead.

---

# 26. Dashboard

The dashboard is useful because FlashScope is inherently visual.

Required pages:

```text
Run Overview
Firmware Comparison
Incident Table
First-Failure Timeline
Latency Distribution
Temperature / Throughput
Error Counter Deltas
Raw Evidence Viewer
```

Use Plotly.

Dashboard should run from saved SQLite/evidence data.

---

# 27. Cloud Use

Cloud is optional.

Useful AWS profile:

```text
S3 -> artifact archive
EC2 -> batch triage runner
CloudWatch -> application logs
Athena optional -> querying Parquet event archive
```

Do not add cloud services merely to make the diagram larger.

FlashScope should run fully locally.

---

# 28. QualiDrive Integration Contract

Input directory:

```text
qualidrive_run/
├── run.json
├── cases/
├── fio/
├── nvme/
├── kernel/
└── system/
```

FlashScope adapter:

```bash
flashscope import-qualidrive <run-dir>
```

This is a high-priority integration because it makes the portfolio coherent.

---

# 29. CI/CD

Pipeline:

```text
lint
unit tests
parser fixture tests
normalization tests
signature tests
incident grouping tests
SQLite migration tests
benchmark smoke test
dashboard smoke test
```

Nightly/manual:

```text
2.3M record benchmark
```

---

# 30. Antigravity Agent Structure

Lead:

```text
flashscope-lead
```

Subagents:

```text
parser-agent
normalization-storage-agent
signature-correlation-agent
benchmark-agent
dashboard-agent
interview-verification-agent
```

Do not parallelize until one source-to-incident vertical slice works.

---

# 31. Antigravity Rules

Create `.agents/rules/project-focus.md`.

```text
PRIMARY GOAL:
Build a defensible SSD telemetry and failure-triage pipeline matching the resume.

PRESERVE EVIDENCE:
Never discard raw input.
Every parsed event must reference raw evidence.

DO NOT OVERCLAIM:
Signature correlation suggests diagnosis.
Do not state hardware/firmware root cause unless evidence supports it.

PERFORMANCE:
The 2.3M-record benchmark must be real.
Do not fake throughput or triage-time reduction.

SCOPE:
Do not build a general observability platform.
Do not add Kafka, Spark, or distributed systems unless a measured need exists.
SQLite remains a core backend because it is part of the resume project.

INTEGRATION:
Prioritize QualiDrive artifact ingestion.

INTERVIEW:
Every incident type must have:
- detection logic
- false-positive risk
- false-negative risk
- required evidence
- likely alternate explanation
```

---

# 32. Master Antigravity Prompt

```text
/goal

Implement FlashScope according to PROJECT_CONSTITUTION.md.

Primary objective:
Substantiate the resume's SSD telemetry, log-correlation, regression-analysis, and failure-triage claims.

Start with one vertical slice:
QualiDrive fixture -> parsers -> normalized schema -> one signature -> one correlated incident -> evidence links -> timeline.

Then implement:
1. remaining parsers
2. common schema
3. signature engine
4. duplicate grouping
5. firmware comparison
6. first-failure timelines
7. SQLite persistence
8. 2.3M-record synthetic/captured benchmark
9. dashboard
10. optional AWS artifact profile

Do not fabricate historical efficiency metrics.

Do not claim synthetic faults are real device failures.

At completion generate interview/FLASHSCOPE_INTERVIEW_GUIDE.md using the actual implementation and evidence.
```

---

# 33. Interview Guide

Generate:

```text
interview/FLASHSCOPE_INTERVIEW_GUIDE.md
```

Minimum categories:

## Telemetry

- SMART/health
- NVMe error log
- kernel logs
- fio latency
- PCIe events
- temperature
- unsafe shutdowns

## Failure diagnosis

- media errors
- controller resets
- I/O timeout
- thermal throttling
- latency regression
- PCIe degradation

## Data engineering

- schema normalization
- timestamps
- event correlation
- deduplication
- indexing
- chunked processing
- SQLite tradeoffs
- pandas scaling

## Validation

- false positive
- false negative
- signature testing
- regression thresholds
- evidence traceability

Minimum:

```text
45 primary questions
90 follow-ups
20 diagnosis scenarios
5 architecture/design questions
```

---

# 34. Mandatory Diagnostic Questions

The final agent must answer:

1. How do you distinguish thermal throttling from ordinary workload variance?
2. Why is a SMART counter delta more useful than an absolute count?
3. How do you correlate fio degradation with a controller reset?
4. Why might a timeout be host-side rather than device-side?
5. How do you avoid grouping unrelated failures?
6. Why preserve raw logs after normalization?
7. How do you compare firmware versions fairly?
8. What does p99 reveal that average latency hides?
9. How do you handle clock skew across log sources?
10. What is the difference between symptom classification and root cause?
11. Why SQLite instead of Elasticsearch?
12. How do you process 2.3M records without exhausting RAM?
13. How do you test regex/signature rules?
14. What makes an incident reproducible?
15. How do you detect a first-failure point?

---

# 35. Definition of Done

FlashScope is complete only when:

- QualiDrive artifacts can be imported
- all required parsers exist
- common schema exists
- raw evidence references are preserved
- required signatures exist
- duplicate grouping works
- first-failure timelines work
- firmware comparison works
- 2.3M-record benchmark succeeds
- SQLite persistence works
- memory/runtime evidence exists
- dashboard works
- regression tests exist
- interview guide exists
