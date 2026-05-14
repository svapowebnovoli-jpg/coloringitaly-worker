#!/usr/bin/env python3
import os, sys, json, requests, logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WORKER_HOST = os.getenv('WORKER_HOST', 'http://coloringitaly-worker:8000')
WORKER_AUTH_TOKEN = os.getenv('WORKER_AUTH_TOKEN', 'S8czRFmFirCxCoMHRsa7Ig_BiVIYbDt75nC1T9z9j40')
N8N_CALLBACK_URL = os.getenv('N8N_CALLBACK_URL', 'https://n8n-o2tu.srv1540181.hstgr.cloud/webhook/8566790a-3c69-4219-a36f-8ff248b85c6b/kdp/callback')
JOBS_PATH = Path(os.getenv('JOBS_PATH', '/srv/coloringitaly/jobs'))

app = Flask(__name__)

def log_action(action, job_id, status, details=""):
    log_path = JOBS_PATH / job_id / "orchestrator.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    msg = f"[{timestamp}] {action} - {status} - {details}\n"
    with open(log_path, 'a') as f:
        f.write(msg)
    logger.info(f"JOB {job_id}: {action} - {status} - {details}")

def notify_worker(job_id, command, chat_id=None, tema=None):
    try:
        url = f"{WORKER_HOST}/{command}"
        payload = {"job_id": job_id, "auth_token": WORKER_AUTH_TOKEN, "callback_url": N8N_CALLBACK_URL}
        if chat_id:
            payload["chat_id"] = chat_id
        if tema:
            payload["tema"] = tema
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        log_action(command.upper(), job_id, "OK", f"Worker: {data.get('status', 'unknown')}")
        return True, data
    except Exception as e:
        error_msg = str(e)
        log_action(command.upper(), job_id, "ERROR", error_msg)
        logger.error(f"Worker call failed for {job_id}: {error_msg}")
        return False, {"error": error_msg}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200

@app.route('/orchestrate', methods=['POST'])
def orchestrate():
    try:
        data = request.get_json() or {}
        command = data.get('command', '').lower()
        job_id = data.get('job_id', '').strip()
        chat_id = data.get('chat_id')
        tema = data.get('tema')
        
        if not job_id:
            return jsonify({"error": "job_id required"}), 400
        if command not in ['importa', 'confeziona']:
            return jsonify({"error": f"command must be 'importa' or 'confeziona', got '{command}'"}), 400
        
        log_action("ORCHESTRATE", job_id, "START", f"command={command}, chat_id={chat_id}, tema={tema}")
        success, response = notify_worker(job_id, command, chat_id, tema)
        
        if success:
            return jsonify({"status": "ok", "job_id": job_id, "command": command, "worker_response": response}), 202
        else:
            return jsonify({"status": "error", "job_id": job_id, "error": response.get('error')}), 500
    except Exception as e:
        logger.error(f"Orchestrate error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    try:
        log_path = JOBS_PATH / job_id / "orchestrator.log"
        if not log_path.exists():
            return jsonify({"status": "not_found"}), 404
        with open(log_path, 'r') as f:
            lines = f.readlines()
        return jsonify({"job_id": job_id, "log_lines": lines[-20:], "total_lines": len(lines)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 ColoringItaly Orchestrator starting...")
    logger.info(f"WORKER_HOST: {WORKER_HOST}")
    logger.info(f"N8N_CALLBACK_URL: {N8N_CALLBACK_URL}")
    JOBS_PATH.mkdir(parents=True, exist_ok=True)
    app.run(host='0.0.0.0', port=8001, debug=False, threaded=True)
