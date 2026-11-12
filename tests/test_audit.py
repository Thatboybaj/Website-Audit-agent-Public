"""Run: pytest -q   (serves the fixture site locally and audits it)"""
import asyncio
import functools
import http.server
import os
import threading

from audit_agent.agent import run_audit

ROOT = os.path.join(os.path.dirname(__file__), "fixture_site")


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_full_audit():
    os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1,localhost"
    srv = serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    r = asyncio.run(run_audit(url, max_pages=10, use_psi=False, use_browser=False, use_ai=False, log=lambda *a: None))
    srv.shutdown()
    assert len(r["areas"]) == 10
    assert 0 <= r["overall_score"] <= 100
    ids = {c["id"]: c["status"] for a in r["areas"] for c in a["checks"]}
    assert ids["broken_links"] in ("warn", "fail")      # fixture has 404s
    assert ids["value_prop"] == "fail"                   # H1 is "Welcome"
    assert ids["vulnerabilities"] != "pass"              # jQuery 1.12.4
    assert ids["utm"] == "fail"                          # internal UTM link
    assert r["action_plan"]["prioritize"]
