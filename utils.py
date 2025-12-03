import os
import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def save_outputs(case_id: str, transcript_lines: List[str], report: Dict, training_rows: List, cases_dir: str = "cases"):
    """Save interview outputs"""
    base = os.path.join(cases_dir, f"{case_id}")
    transcript_path = base + "_transcript.txt"
    report_path = base + "_report.json"
    training_path = base + "_training.jsonl"

    try:
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write("\n".join(transcript_lines))
        logger.info(f"Transcript saved: {transcript_path}")
    except Exception as e:
        logger.error(f"Transcript save failed: {e}")

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved: {report_path}")
    except Exception as e:
        logger.error(f"Report save failed: {e}")

    try:
        with open(training_path, "w", encoding="utf-8") as f:
            for row in training_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        logger.info(f"Training data saved: {training_path}")
    except Exception as e:
        logger.error(f"Training save failed: {e}")
