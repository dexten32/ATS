# Core application constants and configuration mappings

# --- Matching Constants ---
DOMAIN_KEYWORDS = {
    "Architecture": ["architecture", "api design", "system design", "scalable", "microservices", "clean code", "performance", "deployment", "infrastructure"],
    "Security": ["security", "rbac", "auth", "authentication", "authorization", "encryption", "sanitization", "vulnerability", "malicious", "protections"],
    "DevOps": ["docker", "kubernetes", "k8s", "ci/cd", "automation", "observability", "metrics", "monitoring"]
}

# --- Parsing Constants ---
SKILL_MAP = {
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "python": "Python",
    "py": "Python",
    "fastapi": "FastAPI",
    "sql": "SQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "java": "Java",
    "spring": "Spring",
    "angular": "Angular",
    "vue": "Vue",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "oracle": "Oracle",
    "oracle dba": "Oracle DBA",
    "oracle rac": "Oracle RAC",
    "oracle real application clusters": "Oracle RAC",
    "oem cloud control": "Oracle OEM",
    "oracle enterprise manager": "Oracle OEM",
    "data guard": "Data Guard",
    "dataguard": "Data Guard",
    "active data guard": "Data Guard",
    "rman": "RMAN",
    "recovery manager": "RMAN",
    "asm": "ASM",
    "automatic storage management": "ASM",
    "goldengate": "GoldenGate",
    "golden gate": "GoldenGate",
    "rac": "RAC",
    "exadata": "Exadata",
    "oracle 19c": "Oracle 19c",
    "oracle 12c": "Oracle 12c",
    "oracle 11g": "Oracle 11g",
    "sql tuning": "SQL Tuning",
    "performance tuning": "Performance Tuning",
    "pl/sql": "PL/SQL",
    "shell scripting": "Shell Scripting",
    "unix": "Unix",
    "linux": "Linux"
}

SKILL_KEYWORDS = list(set(SKILL_MAP.values()))

SKILL_GROUPS = {
    "Frontend Frameworks": ["React", "Angular", "Vue", "Svelte"],
    "Relational Databases": ["PostgreSQL", "MySQL", "SQL Server", "Oracle", "SQL"],
    "Backend Frameworks": ["FastAPI", "Django", "Flask", "Spring Boot", "Node.js", "Express"],
    "Cloud Providers": ["AWS", "Azure", "GCP"],
}

MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
}

INDUSTRY_DOMAINS = {
    "Healthcare": ["healthcare", "medical", "patient", "clinical", "hospital", "pharma"],
    "Fintech": ["fintech", "banking", "finance", "payment", "crypto", "trading", "ledger"],
    "E-commerce": ["e-commerce", "retail", "shopping", "cart", "marketplace", "order management"],
    "Cybersecurity": ["cybersecurity", "infosec", "threat", "penetration", "incident response", "compliance"],
    "Web Development": ["web", "frontend", "backend", "full stack", "fullstack", "saas", "webapp"],
    "Data & AI": ["data science", "machine learning", "ai", "analytics", "big data", "data engineering", "nlp", "llm", "tensorflow", "pytorch"],
    "Database & Infrastructure": ["database administrator", "dba", "oracle", "mysql", "postgresql", "sql server", "reliability", "availability", "migration", "rman", "asm", "rac", "data guard", "goldengate", "infrastructure", "on-prem", "bare metal"],
    "Cloud & DevOps": ["cloud", "devops", "aws", "azure", "networking", "kubernetes", "docker", "terraform", "ansible", "ci/cd"],
    "Mobile Development": ["ios", "android", "mobile app", "react native", "flutter", "swift"],
    "Game Development": ["game development", "unity", "unreal engine", "gameplay", "3d modeling"],
    "Education/EdTech": ["edtech", "education", "student", "learning platform", "courseware"],
    "Product Management": ["product manager", "product owner", "roadmap", "stakeholder", "prd", "backlog", "user stories", "market research", "customer discovery", "mvp", "product life cycle", "kpis", "metrics", "a/b testing", "go-to-market", "competitive analysis", "strategy"],
    "Design (UI/UX)": ["ui/ux", "designer", "figma", "sketch", "user interface", "user experience", "prototyping", "wireframing"],
    "Sales & Marketing": ["sales", "marketing", "business development", "growth", "advertising", "seo", "customer acquisition"],
    "Human Resources": ["hr", "human resources", "recruiting", "talent acquisition", "onboarding", "payroll"],
    "Project Management": ["project manager", "pmp", "scrum master", "agile", "delivery", "kanban", "sprint"],
    "Management/Leadership": ["director", "vp", "chief", "head of", "general manager", "management"]
}

SENIORITY_SIGNALS = {
    "Lead": ["lead", "led", "architect", "architected", "principal", "head of", "director"],
    "Senior": ["senior", "sr", "technical lead", "mentor", "mentored", "owner", "owned"],
    "Junior": ["junior", "jr", "entry", "intern", "associate"],
}

MATURITY_SIGNALS = {
    "Scale": [
        r"\d+\s*k\s*tps", r"\d+\s*million", r"petabyte", r"scale[d]?\s+(up|out)", 
        r"high\s*availability", r"throughput", r"concurrency", r"latency\s*reduction"
    ],
    "Ownership": [
        r"end-to-end", r"full\s*lifecycle", r"stakeholder\s*management", 
        r"technical\s*roadmap", r"mentored\s*senior", r"built\s*from\s*scratch", r"evangelized"
    ],
    "frontend_depth": [
        r"state management", r"redux", r"context api", r"hooks", r"performance optimization",
        r"core web vitals", r"server side rendering", r"ssr", r"static site generation", r"ssg",
        r"bundle size", r"lazy loading", r"accessibility", r"a11y", r"semantic html"
    ],
    "Optimization": [
        r"perf\s+tuning", r"query\s*optimization", r"cache\s*strat", r"bottleneck\s*analysis",
        r"profiling", r"resource\s*utilization", r"memory\s*leak", r"awr", r"ash", r"addm",
        r"explain\s*plan", r"performance\s*tuning"
    ],
    "HighAvailability": [
        r"data\s*guard", r"rac", r"dgmgrl", r"replication", r"failover", r"disaster\s*recovery",
        r"backup\s*and\s*recovery", r"rman"
    ]
}

POWER_VERBS = [
    "spearheaded", "orchestrated", "accelerated", "engineered", "pioneered",
    "optimized", "architected", "transformed", "modernized", "streamlined",
    "scaled", "mentored", "surpassed", "automated", "negotiated", "executed",
    "leveraged", "centralized", "devised", "forecasted", "maximized",
    "implemented", "developed", "resolved", "migrated", "upgraded", "integrated",
    "established", "orchestrated", "formulated", "pioneered", "reduced",
    "delivered", "cultivated", "strengthened", "designed", "maintained"
]

WEAK_VERBS = [
    "helped", "assisted", "worked on", "involved in", "part of",
    "supported", "contributed to", "participated"
]

ARCHITECTURE_KEYWORDS = [
    "microservices", "distributed systems", "eventual consistency", "cap theorem", 
    "message queues", "caching layers", "sharding", "replication", "partitioning", "idempotency"
]

PRODUCTION_KEYWORDS = [
    "ci/cd", "blue-green", "canary", "observability", "grafana", "prometheus", "elk", 
    "tracing", "incident response", "slat", "slo", "slis", "zerototal downtime"
]

ARCHITECTURAL_PATTERNS = {
    "Workflow & Orchestration": [
        "workflow engine", "state machine", "approval chain", "bpmn", "temporal", "airflow", "orchestration"
    ],
    "Security & Identity": [
        "rbac", "role-based access", "abac", "iam policies", "oauth2", "openid connect", "permissioning"
    ],
    "Observability & Audit": [
        "audit trail", "change tracking", "traceability", "log aggregation", "telemetry", "opentelemetry"
    ],
    "Event-Driven Design": [
        "event-based", "pub/sub", "message broker", "asynchronous processing", "cqrs", "event sourcing"
    ]
}

SOFT_SKILLS_KEYWORDS = ["client", "stakeholder", "collaboration", "communication", "requirement gathering", "presentation"]
FRONTEND_DEPTH_KEYWORDS = ["accessibility", "a11y", "performance tuning", "code splitting", "state management", "design system"]

_SKILL_MAP_NORMALIZED = SKILL_MAP
