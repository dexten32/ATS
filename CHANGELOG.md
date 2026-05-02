# ATS Pro Project Changelog

All notable changes to the ATS Pro project will be documented in this file.

## [2026-05-02] - Clean Code & Architecture Refactoring

### Added
- **Core Constants Module**: Extracted bulky configuration mappings (`SKILL_MAP`, `MATURITY_SIGNALS`, etc.) into `backend/app/core/constants.py` for cleaner domain separation.
- **Project Reorganization**: Established new directories (`scripts/`, `data/`, `docs/`, `tests/`) to cleanly hide loose files from the root repository.
- **Frontend Modularity**: Introduced `Header.jsx` and `Dashboard.jsx` to break down monolithic frontend components.

### Modified
- **Scoring & Parsing Services**: Broken down massive 150+ line methods in `scoring.py` into distinct, single-responsibility helper methods (e.g., `_calculate_skill_score`, `_calculate_maturity_score`).
- **Scraper Script**: Encapsulated the LinkedIn scraper script (`scraping.py`) into a reusable `LinkedInScraper` class and moved it to `scripts/`.
- **Frontend State Management**: Rewrote `App.jsx` to function strictly as a layout wrapper and view router rather than a rendering monolith.

## [2026-02-25] - Cyber Emerald Theme & Advanced UI Refinement

### Added
- **Cyber Emerald Design System**: Implemented a comprehensive new color palette featuring deep navy (`#020617`) and vibrant emerald gradients (`#10b981` to `#3b82f6`).
- **Advanced Background Graphics**: Integrated an SVG hex-grid pattern, animated scan lines, and high-tech "Cyber Glow" orbs for visual depth.
- **Desktop HUD Elements**: Added HUD-inspired technical markers (SYS_SCAN, LATENCY) to fill the desktop void areas on screens wider than 1440px.
- **Enhanced Glassmorphism**: Upgraded card styles with higher backdrop blur (16px), subtle borders, grain texture, and multi-layered shadows.
- **Micro-animations**: Integrated smooth hover transitions, scale effects for buttons, and fade-in animations for result sections.

### Modified
- **style.css**: Completely overhauled with a modern, responsive, and animation-rich design system.
- **app.js**: Updated dynamic UI elements (circular progress, confidence badges, feedback cards) to align with the new Emerald theme.
- **index.html**: Refined structure with semantic improvements, step-by-step numbering for user flow, and enhanced header scaling.

### Fixed
- **Responsive Layout**: Re-engineered the grid system to ensure perfect alignment and readability across all viewports (Mobile, Tablet, and Desktop).
- **CSS Compatibility**: Added standard `background-clip` properties for better cross-browser support.

---

## [2026-02-24] - Maturity & Depth Overhaul

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
