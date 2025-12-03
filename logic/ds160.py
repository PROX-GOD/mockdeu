import os
import re
import json
import datetime
import logging

logger = logging.getLogger(__name__)

class DS160Manager:
    def __init__(self):
        self.path = "ds160.json"

    def load(self):
        if os.path.exists(self.path):
            use = input("Use existing DS-160? (y/n): ").strip().lower()
            if use == "y":
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "case_id" not in data:
                    name = re.sub(r"\W+", "", data.get("name", "applicant")).lower()
                    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    safe_visa_type = data.get('visa_type', 'F1').replace("/", "_").replace("\\", "_")
                    data["case_id"] = f"{name}_{safe_visa_type}_{ts}"
                return data
        return self._collect()

    def _collect(self):
        print("\n--- DS-160 FORM ---\n")
        d = {}
        
        print("Select Visa Type:")
        print("1. F1 (Student)")
        print("2. B1/B2 (Business/Tourism)")
        v_choice = input("Choice (1/2): ").strip()
        d["visa_type"] = "B1/B2" if v_choice == "2" else "F1"
        
        d["name"] = input("Full name: ")
        d["nationality"] = input("Citizenship: ")
        d["home_country"] = input("Home country: ")
        
        if d["visa_type"] == "F1":
            d["education_level"] = input("Highest education level: ")
            d["gpa"] = input("GPA or standing: ")
            d["university"] = input("U.S. University (I-20): ")
            d["major"] = input("Major/Field: ")
            d["sponsor"] = input("Primary sponsor: ")
            d["standardized_tests"] = input("Test Scores (SAT/GRE/TOEFL): ")
        else:
            print("\n--- B1/B2 Specifics ---")
            d["purpose"] = input("Purpose of Trip (Tourism/Business/Medical/Family): ")
            d["duration"] = input("Intended Duration of Stay: ")
            d["job_title"] = input("Current Job Title (or 'Student'/'Unemployed'): ")
            if d["job_title"].lower() not in ["student", "unemployed"]:
                d["company"] = input("Company/Employer Name: ")
                d["income"] = input("Monthly Income: ")
                d["tenure"] = input("How long have you worked there?: ")
            d["travel_history"] = input("Previous Countries Visited: ")
            d["us_family"] = input("Any close relatives in the US? (Yes/No + Relation): ")
            d["who_paying"] = input("Who is paying for this trip?: ")

        name = re.sub(r"\W+", "", d.get("name", "applicant")).lower()
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        safe_visa_type = d['visa_type'].replace("/", "_").replace("\\", "_")
        d["case_id"] = f"{name}_{safe_visa_type}_{ts}"
        
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)
        except Exception as e:
            logger.error(f"Failed saving ds160.json: {e}")
        return d
