"""Real HTTP smoke test, standard library only. BASE_URL may target Nginx or Ingress."""

import json
import os
import urllib.request
import uuid

base = os.environ.get("BASE_URL", "http://localhost:8080").rstrip("/")
headers = {"Content-Type": "application/json"}
if os.environ.get("SMOKE_HOST"):
    headers["Host"] = os.environ["SMOKE_HOST"]


def request(path, data=None, method=None):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(data).encode() if data else None,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.status, dict(response.headers), json.load(response)


status, _, item = request(
    "/api/complaints",
    {
        "text": "Burst water pipe flooding homes since fajr",
        "location": "G-9 smoke " + str(uuid.uuid4()),
    },
)
assert status == 201 and item["category"] == "water", item
assert request("/api/complaints/" + item["id"])[2]["id"] == item["id"]
_, first_headers, stats = request("/api/stats")
_, second_headers, _ = request("/api/stats")
assert {k.lower(): v for k, v in first_headers.items()}["x-cache"] == "MISS", (
    first_headers
)
assert {k.lower(): v for k, v in second_headers.items()}["x-cache"] == "HIT", (
    second_headers
)
assert stats["total"] >= 1
print("PASS: create → retrieve → stats MISS → HIT")
