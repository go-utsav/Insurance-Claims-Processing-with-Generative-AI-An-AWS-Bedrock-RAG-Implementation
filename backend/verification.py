"""
Document verification and fraud detection for insurance claims.
Checks: date logic, required documents, text consistency, format validation.
"""
import re
from datetime import datetime
from typing import Dict, List, Optional


def verify_date_logic(incident_date: str, filing_date: str) -> Dict:
    """Check: filing after incident, within 14 days, incident in past."""
    try:
        inc = datetime.strptime(incident_date, "%Y-%m-%d")
        fil = datetime.strptime(filing_date, "%Y-%m-%d")
        today = datetime.now()
        days_diff = (fil - inc).days
    except (ValueError, TypeError):
        return {"status": "FAIL", "details": "Invalid date format"}

    checks = []
    if fil < inc:
        checks.append({"check": "filing_after_incident", "status": "FAIL", "details": "Filing date is before incident date"})
    else:
        checks.append({"check": "filing_after_incident", "status": "PASS", "details": "Filing date is after incident date"})

    if days_diff > 14:
        checks.append({"check": "within_14_days", "status": "FAIL", "details": f"Filing is {days_diff} days after incident (policy requires ≤14 days)"})
    else:
        checks.append({"check": "within_14_days", "status": "PASS", "details": f"Filing is {days_diff} days after incident (within 14-day limit)"})

    if inc > today:
        checks.append({"check": "incident_in_past", "status": "FAIL", "details": "Incident date is in the future"})
    else:
        checks.append({"check": "incident_in_past", "status": "PASS", "details": "Incident date is in the past"})

    all_pass = all(c["status"] == "PASS" for c in checks)
    return {"status": "PASS" if all_pass else "FAIL", "checks": checks}


def verify_required_documents(estimated_cost: Optional[float], police_report_filed: bool, claim_type: str = "collision") -> Dict:
    """Check: police report required if collision > $2,000."""
    if claim_type.lower() == "collision" and estimated_cost and estimated_cost > 2000:
        if not police_report_filed:
            return {
                "status": "FAIL",
                "details": f"Police report is MANDATORY for collision claims over $2,000. Estimated cost: ${estimated_cost:,.0f}",
            }
        return {"status": "PASS", "details": "Police report provided for collision > $2,000"}
    return {"status": "PASS", "details": "Police report not required (cost ≤ $2,000 or non-collision)"}


def verify_claim_format(claim_id: str) -> Dict:
    """Check: claim ID format matches pattern CL-YYYY-NNN."""
    pattern = r"^CL-\d{4}-\d{3}$"
    if re.match(pattern, claim_id):
        return {"status": "PASS", "details": f"Claim ID format valid: {claim_id}"}
    return {"status": "FAIL", "details": f"Claim ID format invalid. Expected: CL-YYYY-NNN (e.g. CL-2024-001), got: {claim_id}"}


def verify_text_consistency(claim_text: str, police_report_text: Optional[str] = None) -> Dict:
    """
    Basic consistency check: extract dates/names from both and compare.
    For full analysis, use Bedrock to compare documents.
    """
    if not police_report_text:
        return {"status": "SKIP", "details": "No police report provided for comparison"}

    # Extract dates from claim (simple pattern)
    claim_dates = re.findall(r"\d{4}-\d{2}-\d{2}", claim_text)
    report_dates = re.findall(r"\d{4}-\d{2}-\d{2}", police_report_text)

    if not claim_dates or not report_dates:
        return {"status": "SKIP", "details": "Could not extract dates for comparison"}

    # Check if any dates overlap (simple check)
    overlap = set(claim_dates) & set(report_dates)
    if overlap:
        return {"status": "PASS", "details": f"Found matching dates in both documents: {', '.join(overlap)}"}
    return {"status": "WARN", "details": "No matching dates found between claim and police report. May indicate inconsistency."}


def verify_document_legitimacy(
    claim_id: str,
    incident_date: str,
    filing_date: str,
    estimated_cost: Optional[float] = None,
    police_report_filed: bool = False,
    claim_type: str = "collision",
    claim_text: str = "",
    police_report_text: Optional[str] = None,
) -> Dict:
    """
    Main verification function. Returns overall status and detailed checks.
    
    Returns:
        {
            "verification_status": "VERIFIED" | "NEEDS_REVIEW" | "SUSPICIOUS",
            "checks": [...],
            "confidence_score": 0.0-1.0,
            "recommendation": "..."
        }
    """
    checks = []

    # 1. Date logic
    date_check = verify_date_logic(incident_date, filing_date)
    checks.append({"check": "date_logic", **date_check})

    # 2. Required documents
    doc_check = verify_required_documents(estimated_cost, police_report_filed, claim_type)
    checks.append({"check": "required_documents", **doc_check})

    # 3. Format validation
    format_check = verify_claim_format(claim_id)
    checks.append({"check": "format_validation", **format_check})

    # 4. Text consistency (if police report provided)
    consistency_check = verify_text_consistency(claim_text, police_report_text)
    checks.append({"check": "text_consistency", **consistency_check})

    # Calculate overall status
    fails = [c for c in checks if c.get("status") == "FAIL"]
    warns = [c for c in checks if c.get("status") == "WARN"]
    passes = [c for c in checks if c.get("status") == "PASS"]

    if fails:
        verification_status = "SUSPICIOUS"
        confidence = 0.3
        recommendation = f"Found {len(fails)} critical issue(s). Review required."
    elif warns:
        verification_status = "NEEDS_REVIEW"
        confidence = 0.6
        recommendation = f"Found {len(warns)} warning(s). Manual review recommended."
    else:
        verification_status = "VERIFIED"
        confidence = 0.9
        recommendation = "All checks passed. Document appears legitimate."

    return {
        "verification_status": verification_status,
        "checks": checks,
        "confidence_score": confidence,
        "recommendation": recommendation,
        "summary": {
            "total_checks": len(checks),
            "passed": len(passes),
            "warnings": len(warns),
            "failed": len(fails),
        },
    }
