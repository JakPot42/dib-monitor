import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dib_monitor.models import Base, Supplier, FinancialAssessment, OwnershipRecord
from dib_monitor.seed_data import _load_seed_data


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestSeedData:
    def test_seed_creates_two_suppliers(self, db):
        _load_seed_data(db)
        assert db.query(Supplier).count() == 2

    def test_seed_idempotent(self, db):
        _load_seed_data(db)
        _load_seed_data(db)
        assert db.query(Supplier).count() == 2

    def test_arrowhead_is_high_risk(self, db):
        _load_seed_data(db)
        arrowhead = db.query(Supplier).filter(Supplier.name.like("%Arrowhead%")).first()
        assert arrowhead is not None
        assessment = (
            db.query(FinancialAssessment)
            .filter(FinancialAssessment.supplier_id == arrowhead.id)
            .first()
        )
        assert assessment.combined_risk_level in ("HIGH", "CRITICAL")

    def test_meridian_is_low_risk(self, db):
        _load_seed_data(db)
        meridian = db.query(Supplier).filter(Supplier.name.like("%Meridian%")).first()
        assert meridian is not None
        assessment = (
            db.query(FinancialAssessment)
            .filter(FinancialAssessment.supplier_id == meridian.id)
            .first()
        )
        assert assessment.combined_risk_level == "LOW"

    def test_arrowhead_has_cfius_flagged_owner(self, db):
        _load_seed_data(db)
        arrowhead = db.query(Supplier).filter(Supplier.name.like("%Arrowhead%")).first()
        flagged = (
            db.query(OwnershipRecord)
            .filter(
                OwnershipRecord.supplier_id == arrowhead.id,
                OwnershipRecord.cfius_flag.is_(True),
            )
            .count()
        )
        assert flagged >= 1

    def test_meridian_has_no_cfius_flags(self, db):
        _load_seed_data(db)
        meridian = db.query(Supplier).filter(Supplier.name.like("%Meridian%")).first()
        flagged = (
            db.query(OwnershipRecord)
            .filter(
                OwnershipRecord.supplier_id == meridian.id,
                OwnershipRecord.cfius_flag.is_(True),
            )
            .count()
        )
        assert flagged == 0

    def test_distress_probabilities_stored(self, db):
        _load_seed_data(db)
        arrowhead = db.query(Supplier).filter(Supplier.name.like("%Arrowhead%")).first()
        a = (
            db.query(FinancialAssessment)
            .filter(FinancialAssessment.supplier_id == arrowhead.id)
            .first()
        )
        assert a.distress_prob_1yr is not None
        assert a.distress_prob_3yr > a.distress_prob_1yr

    def test_assessment_has_debt_to_ebitda(self, db):
        _load_seed_data(db)
        arrowhead = db.query(Supplier).filter(Supplier.name.like("%Arrowhead%")).first()
        a = (
            db.query(FinancialAssessment)
            .filter(FinancialAssessment.supplier_id == arrowhead.id)
            .first()
        )
        assert a.debt_to_ebitda is not None
        assert a.debt_to_ebitda > 6.0  # Arrowhead is highly leveraged


class TestModels:
    def test_supplier_defaults(self, db):
        s = Supplier(name="Test Corp")
        db.add(s)
        db.commit()
        assert s.sector == "Defense Electronics"
        assert s.dib_category == "Tier 1 Subcontractor"
        assert s.is_demo is False

    def test_ownership_record_cfius_default_false(self, db):
        s = Supplier(name="Test Corp")
        db.add(s)
        db.commit()
        o = OwnershipRecord(supplier_id=s.id, owner_name="Vanguard", pct_owned=10.0)
        db.add(o)
        db.commit()
        assert o.cfius_flag is False
