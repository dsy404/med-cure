import sqlite3
import json
import uuid
import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from ..core.config import settings
from ..schemas.prescription import (
    PrescriptionItemCreate,
    PrescriptionItemUpdate,
    PrescriptionItem,
    PrescriptionSummary,
    PrescriptionResponse
)
from ..schemas.medicine import MedicineProduct, VerificationStatus
from .data_loader import DataLoader
from .medicine_search import MedicineSearchEngine
from .verification import VerificationEngine
from .evidence_graph import EvidenceGraphService

class PrescriptionService:
    def __init__(
        self,
        db_path: Optional[Path] = None,
        data_loader: Optional[DataLoader] = None,
        search_engine: Optional[MedicineSearchEngine] = None,
        verifier: Optional[VerificationEngine] = None,
        evidence_graph: Optional[EvidenceGraphService] = None
    ):
        self.db_path = db_path or settings.EVIDENCE_DB_PATH
        self.data_loader = data_loader
        self.search_engine = search_engine
        self.verifier = verifier
        self.evidence_graph = evidence_graph
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prescriptions (
                    prescription_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prescription_items (
                    item_id TEXT PRIMARY KEY,
                    prescription_id TEXT NOT NULL,
                    original_text TEXT NOT NULL,
                    prescribed_name TEXT NOT NULL,
                    prescribed_strength TEXT,
                    prescribed_form TEXT,
                    prescribed_quantity REAL NOT NULL,
                    user_reference_price_inr REAL,
                    candidate_id TEXT,
                    candidate_name TEXT,
                    candidate_mrp_inr REAL,
                    candidate_unit_size TEXT,
                    verification_status TEXT NOT NULL,
                    is_eligible_for_savings INTEGER NOT NULL,
                    reference_price_inr REAL,
                    comparison_price_inr REAL,
                    calculated_saving_inr REAL,
                    percentage_saving REAL,
                    evidence_decision_id TEXT,
                    ineligible_reason TEXT,
                    clarification_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(prescription_id) REFERENCES prescriptions(prescription_id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rx_items ON prescription_items (prescription_id)")
            conn.commit()

    def create_prescription(self, title: str = "My Prescription") -> PrescriptionResponse:
        rx_id = f"RX-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO prescriptions (prescription_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (rx_id, title, now_iso, now_iso)
            )
            conn.commit()
        return self.get_prescription(rx_id)

    def get_prescription(self, prescription_id: str) -> Optional[PrescriptionResponse]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prescriptions WHERE prescription_id = ?", (prescription_id,))
            rx_row = cursor.fetchone()
            if not rx_row:
                return None

            cursor.execute("SELECT * FROM prescription_items WHERE prescription_id = ? ORDER BY created_at ASC", (prescription_id,))
            item_rows = cursor.fetchall()

        items: List[PrescriptionItem] = []
        for r in item_rows:
            items.append(PrescriptionItem(
                item_id=r["item_id"],
                prescription_id=r["prescription_id"],
                original_text=r["original_text"],
                prescribed_name=r["prescribed_name"],
                prescribed_strength=r["prescribed_strength"],
                prescribed_form=r["prescribed_form"],
                prescribed_quantity=r["prescribed_quantity"],
                user_reference_price_inr=r["user_reference_price_inr"],
                candidate_id=r["candidate_id"],
                candidate_name=r["candidate_name"],
                candidate_mrp_inr=r["candidate_mrp_inr"],
                candidate_unit_size=r["candidate_unit_size"],
                verification_status=r["verification_status"],
                is_eligible_for_savings=bool(r["is_eligible_for_savings"]),
                reference_price_inr=r["reference_price_inr"],
                comparison_price_inr=r["comparison_price_inr"],
                calculated_saving_inr=r["calculated_saving_inr"],
                percentage_saving=r["percentage_saving"],
                evidence_decision_id=r["evidence_decision_id"],
                ineligible_reason=r["ineligible_reason"],
                clarification_status=r["clarification_status"],
                created_at=r["created_at"]
            ))

        summary = self._calculate_prescription_summary(items)

        return PrescriptionResponse(
            prescription_id=rx_row["prescription_id"],
            title=rx_row["title"],
            created_at=rx_row["created_at"],
            updated_at=rx_row["updated_at"],
            items=items,
            summary=summary
        )

    def add_item(self, prescription_id: str, item_in: PrescriptionItemCreate) -> PrescriptionItem:
        rx = self.get_prescription(prescription_id)
        if not rx:
            rx = self.create_prescription()
            prescription_id = rx.prescription_id

        item_id = f"RXI-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        orig_text = item_in.original_text.strip()
        p_name = (item_in.prescribed_name or orig_text).strip()

        # Find best candidate if not explicitly provided
        candidate_prod: Optional[MedicineProduct] = None
        if item_in.selected_candidate_id and self.data_loader:
            candidate_prod = self.data_loader.get_by_id(item_in.selected_candidate_id)
        elif self.search_engine:
            search_res = self.search_engine.search(query=p_name, limit=3, include_ceiling_prices=True)
            if search_res.candidates:
                candidate_prod = search_res.candidates[0].product

        # Verify candidate if found
        v_status = "NEEDS_CLARIFICATION"
        is_eligible = False
        ref_price: Optional[float] = None
        comp_price: Optional[float] = None
        saving_inr: Optional[float] = None
        pct_saving: Optional[float] = None
        dec_id: Optional[str] = None
        ineligible_reason: Optional[str] = None

        if candidate_prod and self.verifier:
            v_res = self.verifier.verify(
                query=p_name,
                candidate=candidate_prod,
                user_ref_price=item_in.user_reference_price_inr,
                user_ref_unit=candidate_prod.unit_size
            )
            v_status = v_res.verification_status.value
            is_eligible = v_res.savings.is_eligible
            ref_price = v_res.savings.reference_price_inr
            comp_price = v_res.savings.comparison_price_inr
            saving_inr = v_res.savings.absolute_saving_inr
            pct_saving = v_res.savings.percentage_saving
            ineligible_reason = v_res.savings.ineligible_reason

            # Record in Evidence Graph
            if self.evidence_graph:
                graph_res = self.evidence_graph.build_and_record(
                    verification=v_res,
                    candidate=candidate_prod,
                    user_ref_price=item_in.user_reference_price_inr,
                    user_ref_unit=candidate_prod.unit_size,
                    input_type="prescription_line"
                )
                dec_id = graph_res.decision_id
            else:
                dec_id = v_res.decision_id

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prescription_items (
                    item_id, prescription_id, original_text, prescribed_name,
                    prescribed_strength, prescribed_form, prescribed_quantity,
                    user_reference_price_inr, candidate_id, candidate_name,
                    candidate_mrp_inr, candidate_unit_size, verification_status,
                    is_eligible_for_savings, reference_price_inr, comparison_price_inr,
                    calculated_saving_inr, percentage_saving, evidence_decision_id,
                    ineligible_reason, clarification_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                prescription_id,
                orig_text,
                p_name,
                item_in.prescribed_strength,
                item_in.prescribed_form,
                item_in.prescribed_quantity or 10.0,
                item_in.user_reference_price_inr,
                candidate_prod.product_id if candidate_prod else None,
                candidate_prod.name if candidate_prod else None,
                candidate_prod.price.amount_inr if (candidate_prod and candidate_prod.price) else None,
                candidate_prod.unit_size if candidate_prod else None,
                v_status,
                1 if is_eligible else 0,
                ref_price,
                comp_price,
                saving_inr,
                pct_saving,
                dec_id,
                ineligible_reason,
                "resolved" if is_eligible else "unresolved",
                now_iso
            ))
            cursor.execute("UPDATE prescriptions SET updated_at = ? WHERE prescription_id = ?", (now_iso, prescription_id))
            conn.commit()

        return PrescriptionItem(
            item_id=item_id,
            prescription_id=prescription_id,
            original_text=orig_text,
            prescribed_name=p_name,
            prescribed_strength=item_in.prescribed_strength,
            prescribed_form=item_in.prescribed_form,
            prescribed_quantity=item_in.prescribed_quantity or 10.0,
            user_reference_price_inr=item_in.user_reference_price_inr,
            candidate_id=candidate_prod.product_id if candidate_prod else None,
            candidate_name=candidate_prod.name if candidate_prod else None,
            candidate_mrp_inr=candidate_prod.price.amount_inr if (candidate_prod and candidate_prod.price) else None,
            candidate_unit_size=candidate_prod.unit_size if candidate_prod else None,
            verification_status=v_status,
            is_eligible_for_savings=is_eligible,
            reference_price_inr=ref_price,
            comparison_price_inr=comp_price,
            calculated_saving_inr=saving_inr,
            percentage_saving=pct_saving,
            evidence_decision_id=dec_id,
            ineligible_reason=ineligible_reason,
            clarification_status="resolved" if is_eligible else "unresolved",
            created_at=now_iso
        )

    def update_item(self, prescription_id: str, item_id: str, update_in: PrescriptionItemUpdate) -> Optional[PrescriptionItem]:
        rx = self.get_prescription(prescription_id)
        if not rx:
            return None
        existing_item = next((i for i in rx.items if i.item_id == item_id), None)
        if not existing_item:
            return None

        p_name = update_in.prescribed_name or existing_item.prescribed_name
        ref_price_user = update_in.user_reference_price_inr if update_in.user_reference_price_inr is not None else existing_item.user_reference_price_inr
        candidate_id = update_in.selected_candidate_id or existing_item.candidate_id

        candidate_prod: Optional[MedicineProduct] = None
        if candidate_id and self.data_loader:
            candidate_prod = self.data_loader.get_by_id(candidate_id)

        v_status = existing_item.verification_status
        is_eligible = existing_item.is_eligible_for_savings
        ref_price = existing_item.reference_price_inr
        comp_price = existing_item.comparison_price_inr
        saving_inr = existing_item.calculated_saving_inr
        pct_saving = existing_item.percentage_saving
        dec_id = existing_item.evidence_decision_id
        ineligible_reason = existing_item.ineligible_reason

        if candidate_prod and self.verifier:
            v_res = self.verifier.verify(
                query=p_name,
                candidate=candidate_prod,
                user_ref_price=ref_price_user,
                user_ref_unit=candidate_prod.unit_size
            )
            v_status = v_res.verification_status.value
            is_eligible = v_res.savings.is_eligible
            ref_price = v_res.savings.reference_price_inr
            comp_price = v_res.savings.comparison_price_inr
            saving_inr = v_res.savings.absolute_saving_inr
            pct_saving = v_res.savings.percentage_saving
            ineligible_reason = v_res.savings.ineligible_reason

            if self.evidence_graph:
                graph_res = self.evidence_graph.build_and_record(
                    verification=v_res,
                    candidate=candidate_prod,
                    user_ref_price=ref_price_user,
                    user_ref_unit=candidate_prod.unit_size,
                    input_type="prescription_clarification"
                )
                dec_id = graph_res.decision_id
            else:
                dec_id = v_res.decision_id

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE prescription_items SET
                    prescribed_name = ?,
                    prescribed_strength = COALESCE(?, prescribed_strength),
                    prescribed_form = COALESCE(?, prescribed_form),
                    prescribed_quantity = COALESCE(?, prescribed_quantity),
                    user_reference_price_inr = ?,
                    candidate_id = ?,
                    candidate_name = ?,
                    candidate_mrp_inr = ?,
                    candidate_unit_size = ?,
                    verification_status = ?,
                    is_eligible_for_savings = ?,
                    reference_price_inr = ?,
                    comparison_price_inr = ?,
                    calculated_saving_inr = ?,
                    percentage_saving = ?,
                    evidence_decision_id = ?,
                    ineligible_reason = ?,
                    clarification_status = ?
                WHERE item_id = ? AND prescription_id = ?
            """, (
                p_name,
                update_in.prescribed_strength,
                update_in.prescribed_form,
                update_in.prescribed_quantity,
                ref_price_user,
                candidate_prod.product_id if candidate_prod else None,
                candidate_prod.name if candidate_prod else None,
                candidate_prod.price.amount_inr if (candidate_prod and candidate_prod.price) else None,
                candidate_prod.unit_size if candidate_prod else None,
                v_status,
                1 if is_eligible else 0,
                ref_price,
                comp_price,
                saving_inr,
                pct_saving,
                dec_id,
                ineligible_reason,
                "manually_confirmed" if is_eligible else "unresolved",
                item_id,
                prescription_id
            ))
            cursor.execute("UPDATE prescriptions SET updated_at = ? WHERE prescription_id = ?", (now_iso, prescription_id))
            conn.commit()

        updated_rx = self.get_prescription(prescription_id)
        return next((i for i in updated_rx.items if i.item_id == item_id), None)

    def remove_item(self, prescription_id: str, item_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM prescription_items WHERE item_id = ? AND prescription_id = ?", (item_id, prescription_id))
            deleted = cursor.rowcount > 0
            if deleted:
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                cursor.execute("UPDATE prescriptions SET updated_at = ? WHERE prescription_id = ?", (now_iso, prescription_id))
            conn.commit()
            return deleted

    def _calculate_prescription_summary(self, items: List[PrescriptionItem]) -> PrescriptionSummary:
        """
        Calculates three separate totals strictly adhering to MedLedger non-negotiables:
        Total A: Confirmed Potential Savings (verified comparisons ONLY)
        Total B: Unresolved items count & audit explanation
        Total C: Informational estimate for unresolved items strictly excluded from confirmed total
        """
        total_items = len(items)
        confirmed_items = [i for i in items if i.is_eligible_for_savings and i.verification_status == "VERIFIED_FOR_PRICE_COMPARISON"]
        unresolved_items = [i for i in items if not i.is_eligible_for_savings or i.verification_status != "VERIFIED_FOR_PRICE_COMPARISON"]

        confirmed_saving = sum((i.calculated_saving_inr or 0.0) for i in confirmed_items)
        confirmed_ref = sum((i.reference_price_inr or 0.0) for i in confirmed_items)
        confirmed_gen = sum((i.comparison_price_inr or 0.0) for i in confirmed_items)
        confirmed_pct = (confirmed_saving / confirmed_ref * 100.0) if confirmed_ref > 0 else 0.0

        # Unresolved estimate: compute informational estimate if candidate price is positive, but keep isolated
        potential_unresolved_saving: float = 0.0
        has_estimable_unresolved = False
        for u in unresolved_items:
            if u.user_reference_price_inr and u.candidate_mrp_inr and u.candidate_mrp_inr > 0:
                diff = u.user_reference_price_inr - u.candidate_mrp_inr
                if diff > 0:
                    potential_unresolved_saving += diff
                    has_estimable_unresolved = True

        unresolved_notes = (
            f"{len(unresolved_items)} item(s) require clinical strength clarification, reference price input, "
            f"or have unlisted catalogue prices. These items are strictly quarantined from confirmed savings."
            if unresolved_items else "All prescription items verified against official price evidence."
        )

        return PrescriptionSummary(
            total_items_count=total_items,
            verified_comparisons_count=len(confirmed_items),
            unresolved_items_count=len(unresolved_items),
            excluded_items_count=len(unresolved_items),
            confirmed_total_savings_inr=round(confirmed_saving, 2),
            confirmed_reference_spend_inr=round(confirmed_ref, 2),
            confirmed_generic_spend_inr=round(confirmed_gen, 2),
            confirmed_savings_percentage=round(confirmed_pct, 1),
            unresolved_summary=unresolved_notes,
            excluded_potential_savings_inr=round(potential_unresolved_saving, 2) if has_estimable_unresolved else None
        )
