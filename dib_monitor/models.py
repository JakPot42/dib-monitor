from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    ticker = Column(String, nullable=True)
    cik = Column(String, nullable=True)          # SEC CIK (zero-padded to 10 digits)
    sector = Column(String, default="Defense Electronics")
    dib_category = Column(String, default="Tier 1 Subcontractor")
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FinancialAssessment(Base):
    __tablename__ = "financial_assessments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    filing_type = Column(String, default="10-K")     # 10-K or 10-Q
    filing_period = Column(String, nullable=True)    # e.g., "FY2025" or "Q3-2025"
    assessed_at = Column(DateTime, default=datetime.utcnow)

    # Extracted financial metrics (all in millions USD)
    revenue_mm = Column(Float, nullable=True)
    total_debt_mm = Column(Float, nullable=True)
    cash_mm = Column(Float, nullable=True)
    ebitda_mm = Column(Float, nullable=True)
    debt_service_annual_mm = Column(Float, nullable=True)
    debt_to_ebitda = Column(Float, nullable=True)

    # Claude-extracted narrative fields
    covenant_summary = Column(Text, nullable=True)
    going_concern_flag = Column(Boolean, default=False)
    going_concern_quote = Column(Text, nullable=True)
    near_term_maturity_mm = Column(Float, nullable=True)
    near_term_maturity_date = Column(String, nullable=True)
    claude_summary = Column(Text, nullable=True)
    extraction_confidence = Column(String, default="demo")   # high/medium/low/demo

    # Monte Carlo results
    distress_prob_1yr = Column(Float, nullable=True)
    distress_prob_2yr = Column(Float, nullable=True)
    distress_prob_3yr = Column(Float, nullable=True)

    # Risk scoring
    financial_risk_score = Column(Integer, nullable=True)    # 0-100
    financial_risk_level = Column(String, nullable=True)     # LOW/MEDIUM/HIGH/CRITICAL
    ownership_risk_score = Column(Integer, nullable=True)
    ownership_risk_level = Column(String, nullable=True)
    combined_risk_score = Column(Integer, nullable=True)
    combined_risk_level = Column(String, nullable=True)


class OwnershipRecord(Base):
    __tablename__ = "ownership_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    assessment_id = Column(Integer, nullable=True, index=True)
    quarter = Column(String, nullable=True)          # e.g., "Q1-2026"
    owner_name = Column(String, nullable=False)
    owner_type = Column(String, default="Institution")
    pct_owned = Column(Float, nullable=True)
    country = Column(String, nullable=True)
    cfius_flag = Column(Boolean, default=False)
    flag_reason = Column(Text, nullable=True)
    risk_level = Column(String, nullable=True)       # HIGH/MEDIUM/LOW
