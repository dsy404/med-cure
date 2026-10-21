import sqlite3
import json
import uuid
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..core.config import settings
from ..schemas.evidence import (
    EvidenceGraphResponse,
    InputEvidenceNode,
    ExtractionNode,
    CandidateNode,
    DecisionNode
)
from ..schemas.verification import VerificationResult
from ..schemas.medicine import MedicineProduct
from .normalizer import extract_attributes, normalize_text
from .brand_aliases import lookup_brand_alias

class EvidenceGraphService:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.EVIDENCE_DB_PATH
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evidence_records (
                    decision_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    candidate_name TEXT NOT NULL,
                    verification_status TEXT NOT NULL,
                    is_savings_eligible INTEGER NOT NULL,
                    savings_inr REAL,
                    evidence_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_query ON evidence_records (query)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidate ON evidence_records (candidate_id)")
            conn.commit()

    def build_and_record(
        self,
        verification: VerificationResult,
        candidate: MedicineProduct,
        user_ref_price: Optional[float] = None,
        user_ref_unit: Optional[str] = None,
        reference_brand: Optional[str] = None,
        input_type: str = "typed_search"
    ) -> EvidenceGraphResponse:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        decision_id = f"DEC-{uuid.uuid4().hex[:10].upper()}"
        verification.decision_id = decision_id
        verification.evidence_chain_id = f"CHAIN-{uuid.uuid4().hex[:8].upper()}"

        query_clean = verification.query.strip()
        query_attrs = extract_attributes(query_clean)
        alias = lookup_brand_alias(query_clean)

        input_node = InputEvidenceNode(
            input_id=f"INP-{uuid.uuid4().hex[:8].upper()}",
            query=query_clean,
            input_type=input_type,
            user_reported_price_inr=user_ref_price,
            user_reported_unit=user_ref_unit,
            reference_brand=reference_brand or (alias.brand_name if alias else None),
            captured_at=now_iso
        )

        extraction_node = ExtractionNode(
            normalized_query=normalize_text(query_clean),
            detected_molecules=query_attrs.ingredients,
            detected_strengths=query_attrs.strengths,
            detected_dosage_form=query_attrs.dosage_form,
            brand_alias_applied=alias.brand_name if alias else None,
            is_combination=bool(len(query_attrs.ingredients) > 1 or (alias is not None and "+" in alias.active_molecule))
        )

        cand_price = candidate.price.amount_inr if candidate.price else 0.0
        candidate_node = CandidateNode(
            product_id=candidate.product_id,
            name=candidate.name,
            catalogue_type=candidate.catalogue_type,
            retrieval_method="EXACT_OR_FUZZY",
            unit_size=candidate.unit_size,
            mrp_inr=cand_price,
            source_file=candidate.source_file,
            provenance=candidate.source_verification_status
        )

        decision_node = DecisionNode(
            decision_id=decision_id,
            verification_status=verification.verification_status,
            is_savings_eligible=verification.savings.is_eligible,
            summary=verification.plain_language_summary,
            abstention_reason=verification.savings.ineligible_reason,
            verified_at=now_iso,
            disclaimer=verification.clinical_disclaimer
        )

        graph_response = EvidenceGraphResponse(
            decision_id=decision_id,
            input_evidence=input_node,
            extraction=extraction_node,
            candidate=candidate_node,
            attribute_checks=verification.attribute_checks,
            price_evidence=verification.comparison_price_evidence or verification.reference_price_evidence,
            savings=verification.savings,
            decision=decision_node,
            software_version=f"MedWise v{settings.VERSION}",
            clinical_disclaimer=verification.clinical_disclaimer
        )

        # Persist to SQLite
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO evidence_records (
                        decision_id, query, candidate_id, candidate_name,
                        verification_status, is_savings_eligible, savings_inr,
                        evidence_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    decision_id,
                    query_clean,
                    candidate.product_id,
                    candidate.name,
                    verification.verification_status.value,
                    1 if verification.savings.is_eligible else 0,
                    verification.savings.absolute_saving_inr or 0.0,
                    graph_response.model_dump_json(),
                    now_iso
                ))
                conn.commit()
        except Exception as e:
            # Fallback gracefully if db error occurs
            pass

        return graph_response

    def get_by_decision_id(self, decision_id: str) -> Optional[EvidenceGraphResponse]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT evidence_json FROM evidence_records WHERE decision_id = ?",
                (decision_id.strip(),)
            )
            row = cursor.fetchone()
            if not row:
                return None
            data = json.loads(row[0])
            return EvidenceGraphResponse(**data)

    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT decision_id, query, candidate_id, candidate_name,
                       verification_status, is_savings_eligible, savings_inr, created_at
                FROM evidence_records
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "decision_id": r[0],
                    "query": r[1],
                    "candidate_id": r[2],
                    "candidate_name": r[3],
                    "verification_status": r[4],
                    "is_savings_eligible": bool(r[5]),
                    "savings_inr": r[6],
                    "created_at": r[7]
                }
                for r in rows
            ]

