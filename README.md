# FlashScope

Enterprise SSD telemetry, log-correlation, regression-analysis, and failure-triage pipeline.

## Capabilities
- **Multi-Source Telemetry Normalization**: Ingests and normalizes fio JSON/JSON+, NVMe SMART counters, NVMe error log entries, kernel dmesg/journalctl, and PCIe link states into a unified common schema.
- **Direct QualiDrive Integration**: Natively ingests QualiDrive qualification run directories (`flashscope import-qualidrive <dir>`) with raw artifact linkage.
- **Failure Signature Engine**: Declarative rule evaluation detecting Media Errors, Controller Resets, I/O Timeouts, Thermal Throttling, Latency Regressions, and Unsafe Shutdown deltas.
- **Incident Deduplication & Correlation**: Groups cascaded log spikes into unified failure incidents with confidence ratings and occurrence counts.
- **First-Failure Timeline**: Reconstructs chronological event progression from baseline I/O to fault onset, failure cascade, and recovery.
- **Firmware Regression Comparison**: Cross-firmware comparative analytics evaluating IOPS/bandwidth regressions, latency shifts, and incident frequencies.
- **High-Performance Ingestion**: Streaming chunked ingestion engine benchmarked on **2.3M+ records** utilizing SQLite with indexed analytical queries.
- **Interactive Dashboard**: Visual inspection interface for triage review, performance comparisons, and raw evidence drill-down.

## Quickstart
```bash
# Import a QualiDrive qualification run
python3 -m flashscope.cli.main import-qualidrive ../QualiDrive/reports/smoke_run --db flashscope.db

# Run automated triage and generate incident report
python3 -m flashscope.cli.main triage --db flashscope.db

# Run 2.3M-record ingestion benchmark
python3 -m flashscope.cli.main benchmark --records 2300000 --db benchmark.db
```
