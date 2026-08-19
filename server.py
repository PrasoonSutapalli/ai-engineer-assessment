"""
Unified Multi-Agent & Real-Time Intelligence Server.
Exposes REST and Web UI endpoints for evaluating Questions 1, 2, 3, and 4.
Operates standalone with standard library HTTP server or ASGI FastAPI.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add parent directory to module search path
sys.path.insert(0, os.path.dirname(__file__))

from q1_voice_agent.agent import HealthInsuranceVoiceAgent
from q2_knowledge_base.kb_store import default_kb
from q2_knowledge_base.benchmark_retrieval import run_retrieval_benchmark
from q3_multilingual_bots.philippines_bot import PhilippinesBancassuranceBot
from q3_multilingual_bots.indonesia_bot import IndonesiaMultifinanceBot
from q4_live_nudges.streaming_pipeline import StreamingCallPipeline
from q4_live_nudges.latency_benchmark import run_latency_benchmarks

# In-memory sessions
q1_agents = {}
ph_bot = PhilippinesBancassuranceBot()
id_bot = IndonesiaMultifinanceBot()
q4_pipeline = StreamingCallPipeline()


class AssessmentHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Handles static web UI assets and REST API endpoints."""

    def __init__(self, *args, **kwargs):
        # Point root directory to web_ui folder
        web_ui_dir = os.path.join(os.path.dirname(__file__), "web_ui")
        super().__init__(*args, directory=web_ui_dir, **kwargs)

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # API: Q2 KB Search
        if path == "/api/q2/search":
            q = query_params.get("q", [""])[0]
            results = default_kb.search(q, top_k=3)
            self._send_json(results)
            return

        # API: Q2 Benchmark
        if path == "/api/q2/benchmark":
            bench = run_retrieval_benchmark()
            self._send_json(bench)
            return

        # API: Q4 Benchmark
        if path == "/api/q4/benchmark":
            bench = run_latency_benchmarks()
            self._send_json(bench)
            return

        # Static Assets
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}

        # API: Q1 Turn
        if path == "/api/q1/turn":
            call_id = payload.get("call_id", "default_call")
            text = payload.get("text", "")
            if call_id not in q1_agents:
                q1_agents[call_id] = HealthInsuranceVoiceAgent(call_id=call_id)
            agent = q1_agents[call_id]
            resp = agent.process_turn(text)
            self._send_json(resp)
            return

        # API: Q3 Turn
        if path == "/api/q3/turn":
            market = payload.get("market", "ph")
            text = payload.get("text", "")
            if market == "ph":
                resp = ph_bot.process_turn(text)
            else:
                resp = id_bot.process_turn(text)
            self._send_json(resp)
            return

        # API: Q4 Process Chunk
        if path == "/api/q4/process_chunk":
            speaker = payload.get("speaker", "CUSTOMER")
            text = payload.get("text", "")
            is_ambient = payload.get("is_ambient", False)
            evt = q4_pipeline.process_chunk(
                chunk_id=len(q4_pipeline.processed_events) + 1,
                timestamp_s=len(q4_pipeline.processed_events) * 2.5,
                speaker=speaker,
                utterance_text=text,
                is_ambient_noise=is_ambient
            )
            self._send_json(evt)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)


def start_server(port: int = 8000):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, AssessmentHTTPRequestHandler)
    print(f"================================================================")
    print(f"🚀 Aegis AI Engineering Evaluation Server Active!")
    print(f"📍 Local Portal: http://127.0.0.1:{port}")
    print(f"================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    start_server(port)
