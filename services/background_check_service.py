# services/background_check_service.py
def run_background_check(candidate_id: str) -> dict:
    # STUB: In production, call a real API (Checkr, etc.)
    # Here, just return “passed” with a fake report link.
    return {
        "status": "passed",
        "report_url": "https://example.com/fake-report.pdf"
    }
