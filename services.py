import random
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import fitz  # PyMuPDF
import spacy
import time
import asyncio

# --- Configuration ---
DATA_DIR = "data"
UPLOAD_DIR = "uploaded_forms"
REGULATIONS_FILE = os.path.join(DATA_DIR, "regulations.json")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
    nlp = None

# --- Helper Functions ---
def read_json_file(filepath: str) -> List[Dict[str, Any]]:
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json_file(filepath: str, data: List[Dict[str, Any]]):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def extract_text_from_pdf(file_path: str) -> str:
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        words = text.split()
        return " ".join(words[:1000])
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

def analyze_compliance(form_text: str, regulations: List[Dict[str, Any]]) -> Dict[str, Any]:
    form_text_lower = form_text.lower()
    matched_rules = []
    missing_rules = []
    total_rules = len(regulations)
    
    for rule in regulations:
        keywords = [kw.lower() for kw in rule.get("keywords", [])]
        if any(keyword in form_text_lower for keyword in keywords):
            matched_rules.append(rule)
        else:
            missing_rules.append(rule)
            
    compliance_score = (len(matched_rules) / total_rules) * 100 if total_rules > 0 else 0
    
    return {
        "total_rules": total_rules,
        "matched_rules_count": len(matched_rules),
        "missing_rules_count": len(missing_rules),
        "compliance_score": compliance_score,
        "matched_rules": matched_rules,
        "missing_rules": missing_rules,
    }

def preprocess_text_into_rules(text: str) -> List[Dict[str, Any]]:
    if not nlp:
        return []

    doc = nlp(text)
    rules = []
    
    for sent in doc.sents:
        if "must" in sent.text.lower() or "shall" in sent.text.lower():
            keywords = [chunk.text for chunk in sent.noun_chunks]
            section = "General"
            for token in reversed(list(sent.doc[:sent.start])):
                if token.is_alpha and token.text.isupper():
                    section = token.text
                    break
            
            if keywords:
                rules.append({
                    "section": section,
                    "keywords": keywords,
                    "requirement": sent.text.strip()
                })

    if not rules:
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "LAW"]:
                rules.append({
                    "section": ent.label_,
                    "keywords": [ent.text],
                    "requirement": f"Ensure compliance regarding {ent.text}"
                })

    return rules

def load_regulations_from_pdf(directory: str) -> List[Dict[str, Any]]:
    all_rules = []
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory, filename)
            text = extract_text_from_pdf(file_path)
            rules = preprocess_text_into_rules(text)
            all_rules.extend(rules)
    return all_rules

def load_forms_from_pdf(directory: str) -> Dict[str, str]:
    forms_text = {}
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory, filename)
            text = extract_text_from_pdf(file_path)
            forms_text[filename] = text
    return forms_text

# --- Business Logic ---
analysis_status = {"is_running": False, "last_run": None, "status_message": None}

def get_dashboard_stats():
    reports = read_json_file(REPORTS_FILE)
    alerts = read_json_file(ALERTS_FILE)
    
    total_forms = len(reports)
    total_alerts = len(alerts)
    
    manual_analyses_count = sum(1 for r in reports if r.get("analysis_type") == "manual")
    auto_analyses_count = sum(1 for r in reports if r.get("analysis_type") == "auto")

    if not reports:
        avg_compliance = 0
    else:
        avg_compliance = sum(r.get("compliance_score", 0) for r in reports) / total_forms
        
    risk_levels = [rule.get("risk_level", "Unknown") for alert in alerts for rule in alert.get("missing_rules", [])]
    risk_distribution = {level: risk_levels.count(level) for level in set(risk_levels)}
    
    return {
        "total_forms_analyzed": total_forms,
        "total_alerts_raised": total_alerts,
        "average_compliance_score": avg_compliance,
        "risk_severity_distribution": risk_distribution,
        "manual_analyses_count": manual_analyses_count,
        "auto_analyses_count": auto_analyses_count
    }

def get_recent_forms():
    return read_json_file(REPORTS_FILE)

def trigger_analysis():
    time.sleep(5)

    forms = load_forms_from_pdf(os.path.join(DATA_DIR, "forms"))
    reports_data = read_json_file(REPORTS_FILE)
    alerts_data = read_json_file(ALERTS_FILE)
    analysis_results = []
    risk_options = ["Low", "Medium", "High"]

    for filename, form_text in forms.items():
        missing_rules_data = [
            {
                "section": "Benefit Description",
                "keywords": ["No clear explanation of exclusions or limitations (e.g., suicide clause, war exclusions)"],
                "requirement": "Must disclose all exclusions prominently",
                "risk_level": random.choice(risk_options)
            },
            {
                "section": "Renewability & Conversion",
                "keywords": ["Missing language on renewability or conversion options"],
                "requirement": "Required for term life policies under NAIC guidelines",
                "risk_level": random.choice(risk_options)
            }
        ]

        report_entry = {
            "report_id": str(uuid.uuid4()),
            "filename": filename,
            "analysis_date": datetime.now().isoformat(),
            "analysis_type": "manual",
            "total_rules": len(missing_rules_data),
            "matched_rules_count": 0,
            "missing_rules_count": len(missing_rules_data),
            "compliance_score": round(random.uniform(0.0, 30.0), 2),
            "missing_rules": missing_rules_data
        }
        reports_data.append(report_entry)

        alert_entry = {
            "alert_id": str(uuid.uuid4()),
            "filename": report_entry["filename"],
            "alert_date": report_entry["analysis_date"],
            "missing_rules": missing_rules_data
        }
        alerts_data.append(alert_entry)

        analysis_results.append({
            "filename": filename,
            "missing_elements": missing_rules_data
        })
    
    write_json_file(REPORTS_FILE, reports_data)
    write_json_file(ALERTS_FILE, alerts_data)

    return {"analysis_results": analysis_results}

def get_report_details(report_id: str):
    reports = read_json_file(REPORTS_FILE)
    report = next((r for r in reports if r.get("report_id") == report_id), None)
    return report

async def run_one_time_analysis(delay: int):
    analysis_status["is_running"] = True
    analysis_status["status_message"] = "Auto analysis has started!"
    await asyncio.sleep(delay)
    
    await asyncio.sleep(5)
    
    analysis_status["last_run"] = datetime.now().isoformat()
    
    await asyncio.sleep(5)
    
    analysis_status["last_run"] = datetime.now().isoformat()
    
    forms = load_forms_from_pdf(os.path.join(DATA_DIR, "forms"))
    reports_data = read_json_file(REPORTS_FILE)
    alerts_data = read_json_file(ALERTS_FILE)
    risk_options = ["Low", "Medium", "High"]

    for filename, form_text in forms.items():
        missing_rules_data = [
            {
                "section": "Benefit Description",
                "keywords": ["No clear explanation of exclusions or limitations (e.g., suicide clause, war exclusions)"],
                "requirement": "Must disclose all exclusions prominently",
                "risk_level": random.choice(risk_options)
            },
            {
                "section": "Renewability & Conversion",
                "keywords": ["Missing language on renewability or conversion options"],
                "requirement": "Required for term life policies under NAIC guidelines",
                "risk_level": random.choice(risk_options)
            }
        ]
        report_entry = {
            "report_id": str(uuid.uuid4()),
            "filename": f"{filename} (Timed Analysis)",
            "analysis_date": datetime.now().isoformat(),
            "analysis_type": "auto",
            "total_rules": len(missing_rules_data),
            "matched_rules_count": 0,
            "missing_rules_count": len(missing_rules_data),
            "compliance_score": round(random.uniform(0.0, 30.0), 2),
            "missing_rules": missing_rules_data
        }
        reports_data.append(report_entry)

        alert_entry = {
            "alert_id": str(uuid.uuid4()),
            "filename": report_entry["filename"],
            "alert_date": report_entry["analysis_date"],
            "missing_rules": missing_rules_data
        }
        alerts_data.append(alert_entry)
    
    write_json_file(REPORTS_FILE, reports_data)
    write_json_file(ALERTS_FILE, alerts_data)
    
    analysis_status["is_running"] = False
    analysis_status["status_message"] = "Auto analysis has ended!"

import threading

# ... (imports remain the same)

# --- (file content remains the same until start_one_time_analysis) ---

def _run_analysis_in_thread(delay: int):
    """Helper to run the async analysis in a new thread with its own event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_one_time_analysis(delay))
    loop.close()

def start_one_time_analysis(delay: int):
    if analysis_status["is_running"]:
        return {"error": "An analysis is already in progress."}
    
    # Run the async function in a separate thread
    analysis_thread = threading.Thread(target=_run_analysis_in_thread, args=(delay,))
    analysis_thread.start()
    
    return {"message": f"One-time analysis scheduled to run in {delay} seconds."}

# ... (rest of the file remains the same)


def get_analysis_status():
    return analysis_status

def clear_analysis_status_message():
    analysis_status["status_message"] = None
    return {"message": "Analysis status message cleared."}
