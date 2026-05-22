"""Diagnostic script to debug StarRocks Stream Load issue."""
import sys
sys.path.insert(0, "hw9")

import pyarrow.parquet as pq
import pyarrow.csv as pa_csv
import io
import base64
import json
import urllib.request

# 1. Check actual column names in customer parquet
t = pq.read_table("./data/customer.parquet")
print("Raw Parquet columns:", t.schema.names)
t = t.rename_columns([c.lower() for c in t.schema.names])
print("Lowercased columns:", t.schema.names)
print("Column types:", [(f.name, str(f.type)) for f in t.schema])

# 2. Check first 3 rows of CSV output with pipe separator
buf = io.BytesIO()
pa_csv.write_csv(t.slice(0, 3), buf, write_options=pa_csv.WriteOptions(include_header=False, delimiter="|"))
print("\nFirst 3 rows (pipe-separated):")
print(buf.getvalue().decode())

# 3. Try a manual stream load with 3 simple unquoted rows
simple_data = b"9999991|TestName1|TestAddress1|1|555-000-0001|100.00|BUILDING|comment1\n9999992|TestName2|TestAddress2|2|555-000-0002|200.00|AUTOMOBILE|comment2\n"
credentials = base64.b64encode(b"root:").decode()

class _PutRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return urllib.request.Request(
            newurl, data=req.data,
            headers={k: v for k, v in req.header_items()},
            method=req.method,
        )

import time
label = f"debug_{int(time.time())}"
req = urllib.request.Request(
    "http://localhost:8030/api/tpch_sf1/customer/_stream_load",
    data=simple_data, method="PUT"
)
req.add_header("Authorization", f"Basic {credentials}")
req.add_header("label", label)
req.add_header("column_separator", "|")
req.add_header("columns", "c_custkey,c_name,c_address,c_nationkey,c_phone,c_acctbal,c_mktsegment,c_comment")
req.add_header("expect", "100-continue")

opener = urllib.request.build_opener(_PutRedirectHandler)
try:
    with opener.open(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
except urllib.request.HTTPError as e:
    result = json.loads(e.read().decode())

print("\nManual stream load result:", json.dumps(result, indent=2))
if result.get("ErrorURL"):
    try:
        with urllib.request.urlopen(result["ErrorURL"].replace("127.0.0.1", "localhost"), timeout=10) as er:
            print("Error log:", er.read().decode()[:500])
    except Exception as ex:
        print("Could not fetch error log:", ex)
