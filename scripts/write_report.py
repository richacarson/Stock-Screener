#!/usr/bin/env python3
"""Helper: reads report JSON from stdin and writes to reports/{ticker}.json"""
import json, sys

data = json.load(sys.stdin)
ticker = data["ticker"]
path = f"/home/user/Stock-Screener/reports/{ticker}.json"
with open(path, "w") as f:
    json.dump(data, f, indent=2)
print(f"Written {ticker}: score={data['overall_score']}, date={data['screen_date']}")
