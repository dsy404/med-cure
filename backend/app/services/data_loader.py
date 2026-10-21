import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from ..core.config import settings
from ..schemas.medicine import MedicineProduct, PriceRecord
from .normalizer import extract_attributes, normalize_text

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.generic_csv_path = self.data_dir / "generic_products_clean.csv"
        self.ceiling_csv_path = self.data_dir / "ceiling_prices_clean.csv"
        self.rs_benchmark_path = self.data_dir / "RS_Session_255_AU_1784_B.csv"
        
        self.generic_products: List[MedicineProduct] = []
        self.ceiling_products: List[MedicineProduct] = []
        self.by_id: Dict[str, MedicineProduct] = {}
        self.rs_benchmarks: List[Dict] = []
        
        self.loaded: bool = False
        self.load_errors: List[str] = []
        self.stats: Dict[str, int] = {
            "generic_count": 0,
            "generic_usable_price_count": 0,
            "ceiling_count": 0,
            "rs_benchmark_count": 0
        }

    def load_all(self) -> Tuple[int, int]:
        """
        Loads cleaned datasets with strict validation and provenance retention.
        """
        self.load_generic_products()
        self.load_ceiling_prices()
        self.load_rs_benchmarks()
        self.loaded = True
        return len(self.generic_products), len(self.ceiling_products)

    def load_generic_products(self) -> None:
        if not self.generic_csv_path.exists():
            msg = f"Generic products file not found at: {self.generic_csv_path}"
            logger.error(msg)
            self.load_errors.append(msg)
            return

        expected_cols = {
            "source_serial_number", "drug_code", "generic_name", "unit_size",
            "mrp_inr_as_listed", "group_name", "price_status",
            "usable_for_price_comparison", "source_file",
            "source_verification_status", "duplicate_generic_name_flag"
        }

        try:
            df = pd.read_csv(self.generic_csv_path, encoding="utf-8")
        except Exception as e:
            msg = f"Failed to parse generic CSV: {e}"
            logger.error(msg)
            self.load_errors.append(msg)
            return

        missing_cols = expected_cols - set(df.columns)
        if missing_cols:
            msg = f"Missing expected columns in generic CSV: {missing_cols}"
            logger.error(msg)
            self.load_errors.append(msg)
            return

        for _, row in df.iterrows():
            drug_code = int(row["drug_code"])
            prod_id = f"GEN-{drug_code}"
            raw_name = str(row["generic_name"]).strip()
            unit_size = str(row["unit_size"]).strip()
            group_name = str(row["group_name"]).strip()
            
            try:
                mrp = float(row["mrp_inr_as_listed"])
            except (ValueError, TypeError):
                mrp = 0.0

            usable = bool(row["usable_for_price_comparison"]) and (mrp > 0.0)
            status = str(row["price_status"])
            
            attrs = extract_attributes(raw_name, unit_size)

            price_rec = PriceRecord(
                amount_inr=mrp,
                currency="INR",
                unit_basis=unit_size,
                price_type="maximum_retail_price_mrp",
                price_status=status,
                usable_for_comparison=usable,
                source_file=str(row["source_file"]),
                source_provenance="Jan Aushadhi Generic Medicine Catalogue (PMBJP)",
                disclaimer="Generic medicine MRP per stated pack. Usable for comparison only if verified positive price."
            )

            product = MedicineProduct(
                product_id=prod_id,
                catalogue_type="generic_product",
                name=raw_name,
                brand_name=None,
                therapeutic_group=group_name,
                unit_size=unit_size,
                price=price_rec,
                attributes=attrs,
                source_file=str(row["source_file"]),
                source_verification_status=str(row["source_verification_status"]),
                duplicate_flag=bool(row["duplicate_generic_name_flag"]),
                metadata={
                    "drug_code": drug_code,
                    "source_serial_number": int(row["source_serial_number"])
                }
            )

            self.generic_products.append(product)
            self.by_id[prod_id] = product
            if usable:
                self.stats["generic_usable_price_count"] += 1

        self.stats["generic_count"] = len(self.generic_products)
        logger.info(f"Loaded {self.stats['generic_count']} generic products ({self.stats['generic_usable_price_count']} price-usable).")

    def load_ceiling_prices(self) -> None:
        if not self.ceiling_csv_path.exists():
            msg = f"Ceiling prices file not found at: {self.ceiling_csv_path}"
            logger.error(msg)
            self.load_errors.append(msg)
            return

        expected_cols = {
            "serial_number", "nlem_version", "formulation", "dosage_strength",
            "so_number", "so_date", "ceiling_price_inr_per_stated_unit",
            "stated_unit", "ceiling_price_raw", "price_type",
            "source_date_as_file_metadata", "source_file", "matching_status"
        }

        try:
            df = pd.read_csv(self.ceiling_csv_path, encoding="utf-8")
        except Exception as e:
            msg = f"Failed to parse ceiling prices CSV: {e}"
            logger.error(msg)
            self.load_errors.append(msg)
            return

        missing_cols = expected_cols - set(df.columns)
        if missing_cols:
            msg = f"Missing expected columns in ceiling CSV: {missing_cols}"
            logger.error(msg)
            self.load_errors.append(msg)
            return

        for _, row in df.iterrows():
            ser_no = int(row["serial_number"])
            prod_id = f"CEIL-{ser_no}"
            formulation = str(row["formulation"]).strip()
            dosage_strength = str(row["dosage_strength"]).strip()
            display_name = f"{formulation} - {dosage_strength}"
            stated_unit = str(row["stated_unit"]).strip()

            try:
                price = float(row["ceiling_price_inr_per_stated_unit"])
            except (ValueError, TypeError):
                price = 0.0

            attrs = extract_attributes(f"{formulation} {dosage_strength}", stated_unit)

            price_rec = PriceRecord(
                amount_inr=price,
                currency="INR",
                unit_basis=stated_unit,
                price_type="ceiling_price_excluding_taxes",
                price_status="official_government_ceiling_price",
                usable_for_comparison=False, # Reference only, not branded retail price!
                source_file=str(row["source_file"]),
                source_provenance=f"NPPA National Pharmaceutical Pricing Authority (S.O. {row['so_number']} dated {row['so_date']})",
                disclaimer="Statutory government ceiling price excluding local taxes (DPCO 2013). This is an upper legal cap, NOT a retail selling price."
            )

            product = MedicineProduct(
                product_id=prod_id,
                catalogue_type="ceiling_price_reference",
                name=display_name,
                brand_name=None,
                therapeutic_group=None,
                unit_size=stated_unit,
                price=price_rec,
                attributes=attrs,
                source_file=str(row["source_file"]),
                source_verification_status=str(row["source_date_as_file_metadata"]),
                duplicate_flag=False,
                metadata={
                    "nlem_version": int(row["nlem_version"]),
                    "so_number": str(row["so_number"]),
                    "so_date": str(row["so_date"]),
                    "matching_status": str(row["matching_status"])
                }
            )

            self.ceiling_products.append(product)
            self.by_id[prod_id] = product

        self.stats["ceiling_count"] = len(self.ceiling_products)
        logger.info(f"Loaded {self.stats['ceiling_count']} ceiling price reference records.")

    def load_rs_benchmarks(self) -> None:
        if not self.rs_benchmark_path.exists():
            return
        try:
            df = pd.read_csv(self.rs_benchmark_path, encoding="utf-8")
            self.rs_benchmarks = df.to_dict(orient="records")
            self.stats["rs_benchmark_count"] = len(self.rs_benchmarks)
        except Exception as e:
            logger.warning(f"Could not load RS session benchmarks: {e}")

    def get_by_id(self, product_id: str) -> Optional[MedicineProduct]:
        return self.by_id.get(product_id)
