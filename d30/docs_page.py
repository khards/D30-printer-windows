"""The HTML docs/usage page served at GET /."""

from __future__ import annotations

_TEMPLATE = """<!doctype html>
<title>D30 Print API</title>
<style>
  body { font-family: -apple-system, "Segoe UI", Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; line-height: 1.5; }
  code, pre { background: #f4f4f4; font-family: Consolas, Menlo, monospace; font-size: 13px; }
  code { padding: 2px 6px; border-radius: 4px; }
  pre { padding: 12px 14px; border-radius: 6px; overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; margin: 16px 0; }
  th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #ddd; vertical-align: top; }
  th { background: #fafafa; }
  h1 { margin-bottom: 4px; }
  h2 { margin-top: 40px; border-bottom: 1px solid #eee; padding-bottom: 6px; }
  .badge { display: inline-block; background: #eee; border-radius: 4px; padding: 2px 8px; font-size: 12px; margin-right: 4px; font-family: Consolas, Menlo, monospace; }
  .muted { color: #666; }
  form { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-top: 16px; max-width: 420px; }
  label { display: block; margin-top: 10px; font-size: 14px; font-weight: 600; }
  label.inline { display: flex; align-items: center; gap: 6px; font-weight: normal; margin-top: 14px; }
  label.inline input { width: auto; }
  input, select { width: 100%; padding: 6px 8px; margin-top: 3px; box-sizing: border-box; font-size: 14px; }
  button { margin-top: 16px; padding: 8px 18px; cursor: pointer; font-size: 14px; }
  #result { white-space: pre-wrap; margin-top: 14px; font-family: Consolas, Menlo, monospace; font-size: 13px; }
  #result.ok { color: #0a7d2c; }
  #result.error { color: #b3241c; }
</style>

<h1>D30 Print API</h1>
<p class="muted">Local HTTP bridge to a Phomemo D30 label printer over its Bluetooth COM port.</p>

<h2>Endpoint</h2>
<p><span class="badge">GET</span><span class="badge">POST</span><span class="badge">PUT</span> <code>__BASE__/api/print</code></p>
<p>Parameters can be sent as a JSON body, or as query string / form fields &mdash; whichever's convenient. GET is handy for a quick test straight from a browser address bar.</p>

<h2>Parameters</h2>
<table>
<tr><th>Name</th><th>Type</th><th>Required</th><th>Description</th></tr>
<tr><td><code>mode</code></td><td>string</td><td>no</td><td><code>text</code> (default) or <code>batch</code></td></tr>
<tr><td><code>text</code></td><td>string</td><td>if mode=text</td><td>Label text. Use <code>\\n</code> for a line break.</td></tr>
<tr><td><code>batch</code></td><td>string</td><td>if mode=batch</td><td>Batch number</td></tr>
<tr><td><code>best_before</code></td><td>string</td><td>if mode=batch</td><td>Best-before date, printed exactly as given (no parsing)</td></tr>
<tr><td><code>product</code></td><td>string</td><td>no</td><td>Optional product name/code, centered and underlined above the batch table when provided (no "Product:" label)</td></tr>
<tr><td><code>length</code></td><td>number</td><td>no</td><td>Label length in mm (default: 40 for text, 30 for batch)</td></tr>
<tr><td><code>count</code></td><td>integer</td><td>no</td><td>Number of copies to print (default: 1)</td></tr>
<tr><td><code>pause_ms</code></td><td>number</td><td>no</td><td>Pause between copies in ms, for die-cut labels with no cut command (default: 250)</td></tr>
<tr><td><code>com_port</code></td><td>string</td><td>no</td><td>COM port, e.g. <code>COM5</code>. The outgoing D30 Bluetooth port is auto-detected if omitted (503 if missing or ambiguous).</td></tr>
</table>

<h2>Examples</h2>

<p>Quick test (GET, from a browser or curl):</p>
<pre>__BASE__/api/print?mode=text&amp;text=Hello!</pre>

<p>From your website:</p>
<pre>fetch("__BASE__/api/print", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    mode: "batch",
    batch: "123456",
    best_before: "04-09-26",
    product: "Olive Oil 500ml",
    count: 3
  })
}).then(r =&gt; r.json()).then(console.log)</pre>

<p>curl:</p>
<pre>curl __BASE__/api/print ^
  -H "Content-Type: application/json" ^
  -d "{\\"mode\\":\\"text\\",\\"text\\":\\"Hello World!\\"}"</pre>

<h2>Response</h2>
<p>Success &mdash; HTTP 200:</p>
<pre>{ "status": "ok", "mode": "text", "com_port": "COM4", "count": 1 }</pre>
<p>Error &mdash; HTTP 400 (bad request), 503 (printer not found/ambiguous), or 502 (serial error):</p>
<pre>{ "status": "error", "message": "..." }</pre>

<h2>Try it</h2>
<form id="try-form">
  <label>Mode
    <select id="f-mode">
      <option value="text">text</option>
      <option value="batch">batch</option>
    </select>
  </label>

  <div id="fields-text">
    <label>Text<input id="f-text" value="Hello World!"></label>
  </div>

  <div id="fields-batch" style="display:none">
    <label>Batch<input id="f-batch" value="123456"></label>
    <label>Best before<input id="f-best-before" value="04-09-26"></label>
    <label>Product (optional)<input id="f-product" value="Olive Oil 500ml" placeholder="e.g. Olive Oil 500ml"></label>
  </div>

  <label>Length (mm, blank = default)<input id="f-length" placeholder="e.g. 30"></label>
  <label>COM port (blank = auto-detect)<input id="f-com-port" placeholder="e.g. COM4"></label>
  <label>Count<input id="f-count" value="1"></label>
  <label>Pause between copies (ms)<input id="f-pause" value="250"></label>

  <button type="submit">Print</button>
</form>
<div id="result"></div>

<script>
  const modeSelect = document.getElementById("f-mode");
  const textFields = document.getElementById("fields-text");
  const batchFields = document.getElementById("fields-batch");
  modeSelect.addEventListener("change", () => {
    const isBatch = modeSelect.value === "batch";
    textFields.style.display = isBatch ? "none" : "block";
    batchFields.style.display = isBatch ? "block" : "none";
  });

  document.getElementById("try-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const result = document.getElementById("result");
    result.className = "";
    result.textContent = "Sending...";

    const body = { mode: modeSelect.value };
    if (modeSelect.value === "batch") {
      body.batch = document.getElementById("f-batch").value;
      body.best_before = document.getElementById("f-best-before").value;
      const product = document.getElementById("f-product").value;
      if (product) body.product = product;
    } else {
      body.text = document.getElementById("f-text").value;
    }
    const length = document.getElementById("f-length").value;
    if (length) body.length = Number(length);
    const comPort = document.getElementById("f-com-port").value;
    if (comPort) body.com_port = comPort;
    body.count = Number(document.getElementById("f-count").value || 1);
    body.pause_ms = Number(document.getElementById("f-pause").value || 250);

    try {
      const resp = await fetch("__BASE__/api/print", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      result.className = resp.ok ? "ok" : "error";
      result.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      result.className = "error";
      result.textContent = String(err);
    }
  });
</script>
"""


def render_docs_page(base_url: str) -> str:
    return _TEMPLATE.replace("__BASE__", base_url.rstrip("/"))
