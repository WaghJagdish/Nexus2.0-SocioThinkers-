import fitz  # PyMuPDF
import logging
import os
import uuid
from typing import Dict, Any, Optional

from core.logging import get_logger
from core.config import get_settings

logger = get_logger(__name__)


# Default field mappings per scheme template
# Maps PDF AcroForm widget names -> internal JSON keys
DEFAULT_FIELD_MAPPINGS = {
    "PM-KISAN-001": {
        "Text_FarmerName": "farmer_name",
        "Text_Aadhaar": "aadhaar_number",
        "Text_BankAcc": "bank_account",
        "Text_IFSC": "bank_ifsc",
        "Text_LandArea": "land_area",
        "Text_Mobile": "mobile_number",
        "Text_State": "state",
        "Text_District": "district",
        "Dropdown_Category": "farmer_category",
    },
    "MAHA-TRACTOR-001": {
        "Text_FarmerName": "farmer_name",
        "Text_Aadhaar": "aadhaar_number",
        "Text_CasteCategory": "caste_category",
        "Text_LandArea": "land_area",
        "Text_Mobile": "mobile_number",
        "Text_State": "state",
        "Text_District": "district",
    },
}


class PDFFormFiller:
    """
    Automates the insertion of user state dictionaries into standardized
    AcroForm PDF templates, securing the output via flattening.
    """

    def __init__(self, template_dir: Optional[str] = None, output_dir: Optional[str] = None):
        settings = get_settings()
        self.template_dir = template_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "templates"
        )
        self.output_dir = output_dir or settings.GENERATED_PDFS_DIR
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_application_form(
        self,
        user_data: Dict[str, Any],
        scheme_id: str,
        output_filename: Optional[str] = None,
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Maps JSON data to PDF widgets, updates values, and flattens the document.
        Returns the path to the generated PDF.
        """
        template_path = os.path.join(self.template_dir, f"{scheme_id}_template.pdf")

        if not os.path.exists(template_path):
            logger.warning(
                f"Template for {scheme_id} not found at {template_path}. "
                "Generating a simple text-based PDF instead."
            )
            return self._generate_text_pdf(user_data, scheme_id, output_filename)

        if not output_filename:
            output_filename = f"form_{scheme_id}_{uuid.uuid4().hex[:8]}.pdf"
        output_path = os.path.join(self.output_dir, output_filename)

        try:
            # Resolve field mapping
            mapping = field_mapping or DEFAULT_FIELD_MAPPINGS.get(scheme_id, {})

            # 1. Open the interactive PDF template
            doc = fitz.open(template_path)

            # 2. Iterate through document pages and extract all interactive widgets
            for page in doc:
                widgets = page.widgets()
                if widgets:
                    for widget in widgets:
                        field_name = widget.field_name
                        if field_name in mapping:
                            json_key = mapping[field_name]
                            if json_key in user_data and user_data[json_key]:
                                widget.field_value = str(user_data[json_key])
                                widget.update()

            # 3. Flattening: Render to image arrays to lock fields (anti-tampering)
            imaged_doc = fitz.open()
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img_page = imaged_doc.new_page(
                    width=page.rect.width, height=page.rect.height
                )
                img_page.insert_image(page.rect, pixmap=pix)

            imaged_doc.save(output_path, deflate=True)
            doc.close()
            imaged_doc.close()

            logger.info(f"Successfully generated flattened PDF at {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate form from template: {e}")
            # Fallback to text PDF
            return self._generate_text_pdf(user_data, scheme_id, output_filename)

    def _generate_text_pdf(
        self,
        user_data: Dict[str, Any],
        scheme_id: str,
        output_filename: Optional[str] = None,
    ) -> str:
        """
        Generates a simple text-based PDF when no AcroForm template is available.
        This ensures form generation always succeeds.
        """
        if not output_filename:
            output_filename = f"form_{scheme_id}_{uuid.uuid4().hex[:8]}.pdf"
        output_path = os.path.join(self.output_dir, output_filename)

        try:
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)  # A4

            # Title
            y = 50
            page.insert_text(
                (50, y),
                f"Application Form — {scheme_id}",
                fontsize=16,
                fontname="helv",
                color=(0, 0, 0),
            )
            y += 30
            page.insert_text(
                (50, y),
                "=" * 60,
                fontsize=10,
                fontname="helv",
            )
            y += 25

            # Field labels and values
            field_labels = {
                "farmer_name": "Farmer Name",
                "aadhaar_number": "Aadhaar Number",
                "bank_account": "Bank Account",
                "bank_ifsc": "Bank IFSC",
                "mobile_number": "Mobile Number",
                "land_area": "Land Area (hectares)",
                "land_area_hectares": "Land Area (hectares)",
                "state": "State",
                "district": "District",
                "farmer_category": "Farmer Category",
                "caste_category": "Caste Category",
            }

            for key, label in field_labels.items():
                value = user_data.get(key, "")
                if value:
                    page.insert_text(
                        (50, y),
                        f"{label}: {value}",
                        fontsize=11,
                        fontname="helv",
                    )
                    y += 22
                    if y > 780:
                        page = doc.new_page(width=595, height=842)
                        y = 50

            # Footer
            y += 20
            page.insert_text(
                (50, y),
                "This form was auto-generated by the Nexus Agricultural Advisory System.",
                fontsize=8,
                fontname="helv",
                color=(0.5, 0.5, 0.5),
            )

            # Flatten by rendering to image
            imaged_doc = fitz.open()
            for pg in doc:
                pix = pg.get_pixmap(dpi=200)
                img_page = imaged_doc.new_page(
                    width=pg.rect.width, height=pg.rect.height
                )
                img_page.insert_image(pg.rect, pixmap=pix)

            imaged_doc.save(output_path, deflate=True)
            doc.close()
            imaged_doc.close()

            logger.info(f"Generated text-based PDF at {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate text PDF: {e}")
            raise

    def list_templates(self) -> list:
        """List available PDF templates."""
        if not os.path.exists(self.template_dir):
            return []
        return [
            f.replace("_template.pdf", "")
            for f in os.listdir(self.template_dir)
            if f.endswith("_template.pdf")
        ]
