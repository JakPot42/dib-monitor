DEMO_MODE = True

APP_TITLE = "DIB Financial Resilience Monitor"
APP_VERSION = "1.0.0"

# SEC EDGAR User-Agent header (required by SEC)
EDGAR_USER_AGENT = "DIB Financial Resilience Monitor jak.potvin@gmail.com"

# Monte Carlo parameters
MC_N_PATHS = 10_000
MC_SEED = 42

# Risk score thresholds
RISK_THRESHOLDS = {
    "CRITICAL": 75,
    "HIGH": 50,
    "MEDIUM": 25,
    "LOW": 0,
}

# Financial score weights (out of 100)
LEVERAGE_WEIGHT = 30     # Debt/EBITDA ratio
DISTRESS_WEIGHT_1YR = 25  # Monte Carlo 1-year distress probability
DISTRESS_WEIGHT_3YR = 15  # Monte Carlo 3-year distress probability
GOING_CONCERN_WEIGHT = 20  # Going concern flag in filing
MATURITY_WEIGHT = 10      # Near-term debt maturity (<24 months)

# Ownership score weights (per flagged owner, additive)
CFIUS_OWNER_WEIGHT = 30
FOREIGN_GOV_OWNER_WEIGHT = 25
HIGH_RISK_COUNTRY_WEIGHT = 15
CONCENTRATION_WEIGHT_25PCT = 20  # owner holds ≥25%
CONCENTRATION_WEIGHT_10PCT = 10  # owner holds ≥10%
CONCENTRATION_WEIGHT_5PCT = 5    # owner holds ≥5%

# Countries flagged as high-risk for DIB ownership analysis
HIGH_RISK_COUNTRIES = {
    "China", "PRC", "Russia", "Iran", "North Korea", "DPRK",
    "Belarus", "Venezuela", "Cuba", "Syria",
}

# DIB supplier categories for classification
DIB_CATEGORIES = [
    "Prime Contractor",
    "Tier 1 Subcontractor",
    "Tier 2 Subcontractor",
    "Critical Sole-Source Supplier",
    "Foreign-Owned Supplier",
]

# Claude model — pinned, never "latest"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
CLAUDE_MAX_TOKENS = 1024
