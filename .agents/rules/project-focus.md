# PRIMARY GOAL:
Build a defensible SSD telemetry and failure-triage pipeline matching the resume.

# PRESERVE EVIDENCE:
Never discard raw input.
Every parsed event must reference raw evidence.

# DO NOT OVERCLAIM:
Signature correlation suggests diagnosis.
Do not state hardware/firmware root cause unless evidence supports it.

# PERFORMANCE:
The 2.3M-record benchmark must be real.
Do not fake throughput or triage-time reduction.

# SCOPE:
Do not build a general observability platform.
Do not add Kafka, Spark, or distributed systems unless a measured need exists.
SQLite remains a core backend because it is part of the resume project.

# INTEGRATION:
Prioritize QualiDrive artifact ingestion.

# INTERVIEW:
Every incident type must have:
- detection logic
- false-positive risk
- false-negative risk
- required evidence
- likely alternate explanation
