"""
OpenClaw Observability Web Server

Simple Flask server for visualizing traces.
"""

from flask import Flask, jsonify, render_template_string, send_from_directory
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openclaw_observability.storage import FileStorage


app = Flask(__name__)
storage = FileStorage()


@app.route("/")
def index():
    """Serve main trace list page."""
    with open(Path(__file__).parent / "static" / "index.html") as f:
        return f.read()


@app.route("/trace/<trace_id>")
def trace_view(trace_id):
    """Serve trace detail page."""
    with open(Path(__file__).parent / "static" / "trace-viewer.html") as f:
        html = f.read()
        return html.replace("{{TRACE_ID}}", trace_id)


@app.route("/api/traces")
def list_traces():
    """API: List all traces."""
    traces = storage.list_traces(limit=100)
    return jsonify(traces)


@app.route("/api/trace/<trace_id>")
def get_trace(trace_id):
    """API: Get trace details."""
    trace = storage.get_trace(trace_id)
    return jsonify(trace)


@app.route("/static/<path:path>")
def serve_static(path):
    """Serve static files."""
    return send_from_directory(Path(__file__).parent / "static", path)


if __name__ == "__main__":
    print("🔍 OpenClaw Observability Server")
    print("=" * 50)
    print("📊 Dashboard: http://localhost:5000")
    print("📁 Trace storage:", storage.base_dir)
    print("=" * 50)
    app.run(debug=True, port=5000)
