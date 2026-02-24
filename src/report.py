"""
report.py - Report generation module for Fraudasaurus.ai

Renders fraud-detection reports in HTML (via Jinja2) and Markdown formats.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Template

# ---------------------------------------------------------------------------
# HTML Jinja2 template
# ---------------------------------------------------------------------------

REPORT_TEMPLATE: str = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title | default("Fraudasaurus.ai - Fraud Detection Report") }}</title>
    <style>
        :root {
            --primary: #1a1a2e;
            --accent: #e94560;
            --bg: #f8f9fa;
            --card-bg: #ffffff;
            --text: #2c2c2c;
            --muted: #6c757d;
            --border: #dee2e6;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: var(--text);
            background: var(--bg);
            line-height: 1.6;
            padding: 0;
        }
        header {
            background: var(--primary);
            color: #ffffff;
            padding: 2rem 2.5rem;
        }
        header h1 { font-size: 1.75rem; font-weight: 700; }
        header p  { color: #adb5bd; margin-top: 0.25rem; font-size: 0.95rem; }
        .container { max-width: 960px; margin: 0 auto; padding: 2rem 1.5rem; }
        section {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
        }
        section h2 {
            font-size: 1.25rem;
            color: var(--primary);
            border-bottom: 2px solid var(--accent);
            padding-bottom: 0.4rem;
            margin-bottom: 1rem;
        }
        section p, section li { font-size: 0.95rem; }
        ul { padding-left: 1.25rem; }
        li { margin-bottom: 0.35rem; }
        .finding {
            border-left: 4px solid var(--accent);
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            background: #fff5f5;
            border-radius: 0 6px 6px 0;
        }
        .finding h3 { font-size: 1rem; color: var(--accent); margin-bottom: 0.3rem; }
        .finding p  { font-size: 0.9rem; color: var(--muted); }
        .finding img {
            max-width: 100%;
            margin-top: 0.75rem;
            border: 1px solid var(--border);
            border-radius: 4px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.75rem;
        }
        th, td {
            text-align: left;
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.9rem;
        }
        th { background: var(--bg); font-weight: 600; }
        footer {
            text-align: center;
            font-size: 0.8rem;
            color: var(--muted);
            padding: 1.5rem 0;
        }
    </style>
</head>
<body>

<header>
    <h1>{{ title | default("Fraudasaurus.ai - Fraud Detection Report") }}</h1>
    <p>Generated {{ generated_at | default("N/A") }}</p>
</header>

<div class="container">

    <!-- Executive Summary -->
    <section>
        <h2>Executive Summary</h2>
        <p>{{ executive_summary | default("No executive summary provided.") }}</p>
    </section>

    <!-- Data Overview -->
    <section>
        <h2>Data Overview</h2>
        {% if data_overview is mapping %}
        <table>
            <thead><tr><th>Metric</th><th>Value</th></tr></thead>
            <tbody>
            {% for key, value in data_overview.items() %}
                <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
            {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p>{{ data_overview | default("No data overview provided.") }}</p>
        {% endif %}
    </section>

    <!-- Findings by Fraud Type -->
    <section>
        <h2>Findings by Fraud Type</h2>
        {% if findings %}
        {% for finding in findings %}
        <div class="finding">
            <h3>{{ finding.name }}</h3>
            <p>{{ finding.description }}</p>
            {% if finding.figure_path %}
            <img src="{{ finding.figure_path }}" alt="{{ finding.name }}">
            {% endif %}
        </div>
        {% endfor %}
        {% else %}
        <p>No findings to report.</p>
        {% endif %}
    </section>

    <!-- CarMeg Profile -->
    <section>
        <h2>CarMeg Profile</h2>
        <p>{{ carmeg_profile | default("No CarMeg profile provided.") }}</p>
    </section>

    <!-- Proposed Solution -->
    <section>
        <h2>Proposed Solution</h2>
        <p>{{ proposed_solution | default("No proposed solution provided.") }}</p>
    </section>

</div>

<footer>
    &copy; Fraudasaurus.ai &mdash; Hackathon Report
</footer>

</body>
</html>
"""

# ---------------------------------------------------------------------------
# Markdown template
# ---------------------------------------------------------------------------

_MARKDOWN_TEMPLATE: str = """\
# {{ title | default("Fraudasaurus.ai - Fraud Detection Report") }}

*Generated {{ generated_at | default("N/A") }}*

---

## Executive Summary

{{ executive_summary | default("No executive summary provided.") }}

---

## Data Overview

{% if data_overview is mapping -%}
| Metric | Value |
|--------|-------|
{% for key, value in data_overview.items() -%}
| {{ key }} | {{ value }} |
{% endfor %}
{%- else -%}
{{ data_overview | default("No data overview provided.") }}
{%- endif %}

---

## Findings by Fraud Type

{% if findings -%}
{% for finding in findings %}
### {{ finding.name }}

{{ finding.description }}

{% if finding.figure_path -%}
![{{ finding.name }}]({{ finding.figure_path }})
{%- endif %}

{% endfor %}
{%- else -%}
No findings to report.
{%- endif %}

---

## CarMeg Profile

{{ carmeg_profile | default("No CarMeg profile provided.") }}

---

## Proposed Solution

{{ proposed_solution | default("No proposed solution provided.") }}

---

*Fraudasaurus.ai - Hackathon Report*
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(
    context: Dict[str, Any],
    output_path: str = "output/report.html",
) -> str:
    """Render the HTML fraud-detection report.

    Parameters
    ----------
    context : dict
        Template variables.  Expected keys:

        * ``title`` (str) -- report title
        * ``generated_at`` (str) -- timestamp string
        * ``executive_summary`` (str)
        * ``data_overview`` (str **or** dict mapping metric names to values)
        * ``findings`` (list of dicts, each with ``name``, ``description``,
          and optional ``figure_path``)
        * ``carmeg_profile`` (str)
        * ``proposed_solution`` (str)

    output_path : str
        Destination file path.  Parent directories are created if needed.

    Returns
    -------
    str
        The rendered HTML string.
    """
    template = Template(REPORT_TEMPLATE)
    html = template.render(**context)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    return html


def generate_markdown_report(
    context: Dict[str, Any],
    output_path: str = "output/report.md",
) -> str:
    """Render the Markdown fraud-detection report.

    Parameters
    ----------
    context : dict
        Same schema as :func:`generate_report`.
    output_path : str
        Destination file path.  Parent directories are created if needed.

    Returns
    -------
    str
        The rendered Markdown string.
    """
    template = Template(_MARKDOWN_TEMPLATE)
    md = template.render(**context)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")

    return md
