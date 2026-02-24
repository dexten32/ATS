# ATS Pro Project Changelog

All notable changes to the ATS Pro project will be documented in this file.

## [2026-02-24] - Maturity & Depth Overhaul (Today)

### Added
- **Architectural Pattern Detection**: Shifted from keyword matching to detecting functional system clusters:
    - **Workflow & Orchestration**: Recognizes state machines, approval chains, and engines (Airflow/Temporal).
    - **Security & Identity**: Verifies depth in RBAC, ABAC, and modern identity patterns.
    - **Observability & Auditability**: Detects audit trails and traceability signals.
    - **Event-Driven Design**: Identifies Pub/Sub, CQRS, and asynchronous processing patterns.
- **System Thinking Bonus**: Implemented a dynamic multiplier (up to 1.2x) for candidates demonstrating complex architectural patterns.
- **Strategic Maturity Pillar**: Promoted Engineering Maturity to a core scoring factor (35% weight).
- **UX & UI Polish**:
    - **Clear Content Button**: Added a dedicated button to reset the Job Description field.
    - **Styled Scrollbars**: Implemented custom, low-profile scrollbars for text areas.
    - **Discrete Resizer**: Refined the textarea resize handle and scrollbar corner to be completely transparent, eliminating 'white box' glitches during overflow.

### Fixed
- **NameError in ScoringService**: Fixed a regression where `missing_preferred` was undefined in the `calculate_score` return dictionary.
    - **Scale Signals**: Detects mentions of "100k+ users", "millions of records", "high throughput".
    - **Production Readiness**: Detects "CI/CD", "Monitoring", "Observability", "Unit Testing", "SLAs".
    - **Architecture Depth**: Detects "Microservices", "Distributed Systems", "Event-driven architecture".
- **Depth Multipliers**: Implemented logic in `ScoringService` that applies multipliers (up to 1.2x) to skill scores based on detected impact and scale signals.
- **Detailed Maturity Feedback**: The system now provides strategic advice on architectural gaps, lack of scale metrics, and production ownership.

### Modified
- **ScoringService**: Integrated Maturity Score (25% weight) into the overall match calculation.
- **ParsingService**: Added `extract_maturity_signals` and updated `parse_job_description` to extract maturity requirements from JDs.
- **API (endpoints.py)**: Updated `/analyze` response to include `maturity_match` and `detailed_maturity` metrics.

---

## [2026-02-24] - Strategic Logic Overhaul

### Added
- **Mandatory Skill Gates**: Implemented logic to distinguish between "Required" and "Preferred" skills. Missing a mandatory skill now triggers a 30% penalty.
- **Domain Awareness**: Added industry classification (Fintech, Health, E-commerce, Cybersecurity) for both Resumes and JDs. Alignment rewards are now applied.
- **Seniority Analysis**: Added professional signal detection ("Lead", "Architect", "Mentor") to match candidate seniority against JD expectations.
- **Alternative Tech Compensation**: Implemented partial credit (alternative match) when a mandatory skill is missing but an equivalent (e.g., React vs Vue) is present.

### Modified
- **Experience Extraction**: Upgraded to handle date ranges (e.g., "Nov 2023 - Sep 2024") and calculate precise totals.
- **Semantic Matching**: Enhanced `SemanticMatchingService` with domain-specific keyword boosting for Architectural and Security terms.
- **Confidence Engine**: Revamped to calculate confidence based on "Parsing Certainty" (data field availability) rather than just the final score.

---

## [2026-02-24] - Infrastructure & UI Stabilization

### Fixed
- **Connectivity Issues**: Resolved CORS errors by hosting the frontend directly from the FastAPI backend using `StaticFiles`.
- **Asset Loading**: Fixed CSS/JS pathing issues in `index.html` for relative serving.
- **Loader Persistence**: Fixed a CSS bug where the analyzing loader remained visible after completion despite the `.hidden` class.

### Modified
- **API Architecture**: Updated all imports to absolute paths for stability.
- **UI Design**: Enhanced dashboard with real-time circular progress bars, detail-rich match bars, and informative badges.
