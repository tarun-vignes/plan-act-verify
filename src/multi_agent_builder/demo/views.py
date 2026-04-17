from __future__ import annotations

import json


def render_home_page(initial_payload: dict[str, object] | None) -> str:
    initial_state = json.dumps(initial_payload)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Codex Creator Challenge Demo</title>
  <style>
    :root {{
      --panel: rgba(255, 250, 242, 0.92);
      --ink: #13261d;
      --muted: #5c6d62;
      --line: rgba(19, 38, 29, 0.12);
      --accent: #c85f28;
      --accent-dark: #8f3810;
      --signal: #116149;
      --warning: #b85c1f;
      --shadow: 0 24px 70px rgba(20, 26, 19, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Aptos", "Trebuchet MS", "Segoe UI Variable", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(200, 95, 40, 0.18), transparent 32%),
        radial-gradient(circle at bottom right, rgba(17, 97, 73, 0.18), transparent 28%),
        linear-gradient(135deg, #f9f2e8 0%, #efe8dd 45%, #f7f1e8 100%);
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(19, 38, 29, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(19, 38, 29, 0.02) 1px, transparent 1px);
      background-size: 28px 28px;
      mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.8), transparent 92%);
    }}
    .shell {{
      width: min(1200px, calc(100vw - 28px));
      margin: 0 auto;
      padding: 28px 0 56px;
      position: relative;
      z-index: 1;
    }}
    .hero, .grid, .summary-grid, .milestones, .dual {{
      display: grid;
      gap: 18px;
    }}
    .hero {{
      grid-template-columns: 1.15fr 0.85fr;
      margin-bottom: 24px;
    }}
    .grid {{
      grid-template-columns: 1fr 1fr;
    }}
    .summary-grid {{
      grid-template-columns: repeat(3, 1fr);
    }}
    .milestones {{
      grid-template-columns: repeat(6, 1fr);
    }}
    .dual {{
      grid-template-columns: 1fr 1fr;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
    }}
    .hero-copy, .hero-aside, .builder, .results, .copy, .deploy {{
      padding: 28px;
    }}
    .hero-copy {{
      position: relative;
      overflow: hidden;
    }}
    .hero-copy::after {{
      content: "";
      position: absolute;
      right: -80px;
      top: -80px;
      width: 220px;
      height: 220px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(200, 95, 40, 0.22), transparent 70%);
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(255, 248, 239, 0.92);
      border: 1px solid rgba(200, 95, 40, 0.16);
      color: var(--accent-dark);
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.14em;
      font-weight: 700;
    }}
    .eyebrow::before {{
      content: "";
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 0 4px rgba(200, 95, 40, 0.15);
    }}
    h1 {{
      margin: 18px 0 14px;
      max-width: 9ch;
      font-family: "Georgia", "Palatino Linotype", serif;
      font-size: clamp(2.7rem, 6vw, 4.8rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }}
    h2 {{
      margin: 0 0 10px;
      font-size: 1.5rem;
      letter-spacing: -0.03em;
    }}
    h3 {{
      margin: 0 0 8px;
      font-size: 0.95rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .lede, .subtle, ul.clean, .event-list {{
      color: var(--muted);
      line-height: 1.6;
    }}
    .lede {{
      margin: 0 0 24px;
      max-width: 60ch;
    }}
    .hero-stats {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-top: 24px;
    }}
    .stat, .mini-card, .summary-card, .milestone-card, .event-shell {{
      padding: 16px;
      border-radius: 18px;
      background: rgba(255, 248, 239, 0.88);
      border: 1px solid rgba(19, 38, 29, 0.08);
    }}
    .stat strong, .summary-card strong {{
      display: block;
      margin-bottom: 6px;
      font-size: 1.45rem;
    }}
    .summary-card h3 {{
      font-size: 0.82rem;
      color: var(--muted);
    }}
    form {{
      display: grid;
      gap: 16px;
    }}
    textarea {{
      width: 100%;
      min-height: 180px;
      resize: vertical;
      padding: 18px 20px;
      border-radius: 18px;
      border: 1px solid rgba(19, 38, 29, 0.12);
      background: rgba(255, 255, 255, 0.8);
      color: var(--ink);
      font: inherit;
    }}
    .controls, .chips, .artifact-links, .detail-list, .result-top {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }}
    button, .chip, .artifact-links a, .link-chip {{
      border-radius: 999px;
      padding: 10px 14px;
      font: inherit;
      text-decoration: none;
      border: 1px solid rgba(19, 38, 29, 0.08);
    }}
    button {{
      cursor: pointer;
      font-weight: 700;
      transition: transform 180ms ease, box-shadow 180ms ease;
    }}
    .primary {{
      border: 0;
      padding: 14px 22px;
      background: linear-gradient(135deg, var(--accent), #de7f42);
      color: #fff;
      box-shadow: 0 16px 30px rgba(200, 95, 40, 0.22);
    }}
    .ghost {{
      background: rgba(19, 38, 29, 0.04);
      color: var(--ink);
    }}
    .chip, .artifact-links a, .link-chip {{
      background: rgba(255, 248, 239, 0.92);
      color: var(--ink);
    }}
    .primary:hover, .artifact-links a:hover {{
      transform: translateY(-1px);
    }}
    .status {{
      min-height: 24px;
      color: var(--signal);
      font-weight: 700;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(17, 97, 73, 0.09);
      color: var(--signal);
      font-size: 0.88rem;
      font-weight: 700;
    }}
    .pill.running {{
      background: rgba(184, 92, 31, 0.1);
      color: var(--warning);
    }}
    .event-shell {{
      padding: 18px;
    }}
    .event-list {{
      margin: 0;
      padding-left: 18px;
      max-height: 240px;
      overflow: auto;
    }}
    .milestone-card {{
      min-height: 92px;
    }}
    .milestone-card span {{
      display: block;
      font-size: 0.76rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .milestone-card strong {{
      display: block;
      font-size: 0.98rem;
      margin-bottom: 6px;
    }}
    .state-pending {{ color: var(--muted); }}
    .state-running, .state-retrying {{ color: var(--warning); }}
    .state-completed {{ color: var(--signal); }}
    .state-failed {{ color: #8a1c1c; }}
    .stack {{
      display: grid;
      gap: 24px;
      margin-top: 24px;
    }}
    ul.clean {{
      margin: 0;
      padding-left: 18px;
    }}
    code.inline {{
      padding: 2px 6px;
      border-radius: 6px;
      background: rgba(19, 38, 29, 0.08);
    }}
    @media (max-width: 1050px) {{
      .hero, .grid, .dual {{
        grid-template-columns: 1fr;
      }}
      .milestones {{
        grid-template-columns: repeat(3, 1fr);
      }}
    }}
    @media (max-width: 720px) {{
      .shell {{
        width: min(100vw - 18px, 100%);
        padding-top: 12px;
      }}
      .hero-copy, .hero-aside, .builder, .results, .copy, .deploy {{
        padding: 22px;
      }}
      .hero-stats, .summary-grid, .milestones {{
        grid-template-columns: 1fr;
      }}
      h1 {{
        max-width: none;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="panel hero-copy">
        <div class="eyebrow">Codex Creator Challenge Demo</div>
        <h1>From product idea to working prototype.</h1>
        <p class="lede">This demo calls the same orchestrator used by the CLI. It produces a specification, architecture, runnable implementation, tests, evaluation, and a build summary from one prompt, and now shows the build progressing live in the browser.</p>
        <div class="hero-stats">
          <div class="stat"><strong>5</strong>agent layers</div>
          <div class="stat"><strong>1</strong>shared orchestration core</div>
          <div class="stat"><strong>Live</strong>progress updates</div>
        </div>
      </div>
      <aside class="panel hero-aside">
        <div class="mini-card"><h3>Plan</h3><p class="subtle">Requirements, user stories, contracts, assumptions, and gaps are produced before code generation starts.</p></div>
        <div class="mini-card"><h3>Act</h3><p class="subtle">The implementation agent generates a real prototype aligned to the architecture artifact.</p></div>
        <div class="mini-card"><h3>Verify</h3><p class="subtle">Testing and evaluation enforce quality gates and feed failures back into the loop.</p></div>
      </aside>
    </section>

    <section class="grid">
      <div class="panel builder">
        <h2>Build Something</h2>
        <p class="subtle">Enter a product concept. The orchestrator will run the full plan-act-verify pipeline and stream milestone progress into the panel on the right.</p>
        <form id="build-form">
          <label for="idea-input">Product idea</label>
          <textarea id="idea-input" name="idea" placeholder="Example: Internal workflow assistant for university career services teams that triages student requests and suggests next actions."></textarea>
          <div class="controls">
            <button class="primary" id="build-button" type="submit">Run Autonomous Build</button>
            <button class="ghost" id="fill-button" type="button">Load Competition Prompt</button>
          </div>
          <div class="status" id="status-line" aria-live="polite"></div>
          <div class="chips">
            <button class="chip" type="button" data-idea="Persistent quiz game with scoring logic for student clubs">Quiz game</button>
            <button class="chip" type="button" data-idea="Beauty consultation agent for local salon teams">Beauty consultation</button>
            <button class="chip" type="button" data-idea="Data insight pipeline for CSV uploads from campus operations teams">CSV insights</button>
            <button class="chip" type="button" data-idea="Sustainability tracker for university events and procurement programs">Sustainability tracker</button>
          </div>
        </form>
      </div>

      <div class="panel results">
        <h2>Live Build View</h2>
        <p class="subtle">This panel follows the current build job and links directly to the generated requirements, architecture, tests, evaluation, and summary artifacts when it finishes.</p>
        <div id="result-root"></div>
      </div>
    </section>

    <div class="stack">
      <section class="grid">
        <div class="panel copy">
          <h2>Submission Highlights</h2>
          <div class="dual">
            <div><h3>Why it stands out</h3><ul class="clean"><li>It does not stop at planning.</li><li>CLI, tests, and browser all share one orchestration core.</li><li>Every layer has a clear interface for stronger agents later.</li></ul></div>
            <div><h3>Employer signal</h3><ul class="clean"><li>Agent orchestration and failure recovery</li><li>Contract-first design</li><li>Generated tests and quality gates</li><li>Deployment-ready packaging</li></ul></div>
          </div>
        </div>
        <div class="panel deploy">
          <h2>Deployable Shape</h2>
          <p class="subtle">The repo ships with a standard-library demo server, CI, a hardened Dockerfile, and deployment notes. Run it locally with <code class="inline">python -m multi_agent_builder.demo.server</code> or inside a container.</p>
          <div class="detail-list"><span class="link-chip">Async demo jobs</span><span class="link-chip">Container packaging</span><span class="link-chip">Artifact links</span><span class="link-chip">Submission-ready copy</span></div>
        </div>
      </section>
    </div>
  </div>

  <script>
    const initialPayload = {initial_state};
    const form = document.getElementById("build-form");
    const ideaInput = document.getElementById("idea-input");
    const statusLine = document.getElementById("status-line");
    const resultRoot = document.getElementById("result-root");
    const buildButton = document.getElementById("build-button");
    const fillButton = document.getElementById("fill-button");
    const defaultIdea = "Build a production-style multi-agent system that takes a product idea and autonomously designs, implements, tests, and evaluates a working prototype.";
    let activeJobId = null;
    let pollTimer = null;

    function escapeHtml(value) {{
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }}

    function renderList(items) {{
      if (!items || !items.length) return "<li>None</li>";
      return items.map((item) => `<li>${{escapeHtml(item)}}</li>`).join("");
    }}

    function renderArtifacts(links) {{
      if (!links) return "";
      return Object.entries(links)
        .map(([label, href]) => `<a href="${{escapeHtml(href)}}" target="_blank" rel="noreferrer">${{escapeHtml(label)}}</a>`)
        .join("");
    }}

    function renderMilestones(items) {{
      if (!items || !items.length) return "";
      return items.map((item) => `
        <div class="milestone-card">
          <span>${{escapeHtml(item.name)}}</span>
          <strong class="state-${{escapeHtml(item.status)}}">${{escapeHtml(item.status)}}</strong>
          <small>${{escapeHtml(item.owner || "autonomous agent")}}</small>
        </div>`).join("");
    }}

    function renderEvents(events) {{
      if (!events || !events.length) return "<li>No events yet.</li>";
      return events.map((event) => `<li><strong>${{escapeHtml(event.agent)}}</strong>: ${{escapeHtml(event.detail)}}</li>`).join("");
    }}

    function renderResult(payload) {{
      if (!payload) {{
        resultRoot.innerHTML = "<p class='subtle'>Run the builder to populate this view.</p>";
        return;
      }}
      const job = payload.job || null;
      const summary = payload.summary || null;
      const pillClass = job && job.status !== "completed" ? "pill running" : "pill";
      const pillLabel = job ? job.status.toUpperCase() : (summary ? summary.status.toUpperCase() : "READY");
      const headline = summary ? summary.product_name : (job ? job.idea : "No build yet");
      const summaryCards = summary ? `
        <div class="summary-grid">
          <div class="summary-card"><h3>Run ID</h3><strong>${{escapeHtml(summary.run_id)}}</strong><span>${{escapeHtml(summary.test_results_summary)}}</span></div>
          <div class="summary-card"><h3>Duration</h3><strong>${{escapeHtml(String(summary.total_duration_ms))}} ms</strong><span>${{escapeHtml(((summary.iterations || []).map((item) => item.result).join(" | ")) || "No iterations logged")}}</span></div>
          <div class="summary-card"><h3>Milestones</h3><strong>${{escapeHtml(String((summary.milestones || []).length))}}</strong><span>${{escapeHtml(((summary.milestones || []).map((item) => item.name).join(", ")) || "No milestones")}}</span></div>
        </div>` : "";
      const milestoneCards = job ? `<div class="milestones">${{renderMilestones(job.milestones)}}</div>` : "";
      const eventList = job ? `<div class="event-shell"><h3>Recent Events</h3><ol class="event-list">${{renderEvents(job.events)}}</ol></div>` : "";
      const riskAndRoadmap = summary ? `
        <div class="dual">
          <div class="summary-card"><h3>Risk Assessment</h3><ul class="clean">${{renderList(summary.risk_assessment)}}</ul></div>
          <div class="summary-card"><h3>Next Iteration Roadmap</h3><ul class="clean">${{renderList(summary.next_iteration_roadmap)}}</ul></div>
        </div>` : "";
      const artifacts = summary ? `<div><h3>Artifacts</h3><div class="artifact-links">${{renderArtifacts(payload.artifact_links)}}</div></div>` : "";
      resultRoot.innerHTML = `
        <div class="result-top">
          <span class="${{pillClass}}">${{escapeHtml(pillLabel)}}</span>
          <strong>${{escapeHtml(headline)}}</strong>
        </div>
        <p class="subtle">${{escapeHtml(job ? job.current_message : (summary ? summary.product_idea : "Run the builder to populate this view."))}}</p>
        ${{summaryCards}}
        ${{milestoneCards}}
        ${{eventList}}
        ${{artifacts}}
        ${{riskAndRoadmap}}
      `;
    }}

    async function pollJob(jobId) {{
      try {{
        const response = await fetch(`/api/builds/${{encodeURIComponent(jobId)}}`);
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "Unable to fetch job status");
        renderResult(payload);
        statusLine.textContent = payload.job.current_message;
        if (payload.job.status === "completed") {{
          buildButton.disabled = false;
          statusLine.textContent = `Build completed in ${{payload.summary.total_duration_ms}} ms.`;
          activeJobId = null;
          clearInterval(pollTimer);
          pollTimer = null;
        }} else if (payload.job.status === "failed") {{
          buildButton.disabled = false;
          statusLine.textContent = payload.job.error || "Build failed.";
          activeJobId = null;
          clearInterval(pollTimer);
          pollTimer = null;
        }}
      }} catch (error) {{
        buildButton.disabled = false;
        statusLine.textContent = error.message;
        activeJobId = null;
        if (pollTimer) {{
          clearInterval(pollTimer);
          pollTimer = null;
        }}
      }}
    }}

    async function startBuild(idea) {{
      buildButton.disabled = true;
      statusLine.textContent = "Queueing build job...";
      renderResult({{
        job: {{
          status: "queued",
          idea,
          current_message: "Waiting for the orchestrator to start",
          events: [],
          milestones: [],
        }}
      }});
      try {{
        const response = await fetch("/api/build", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ idea }})
        }});
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "Build failed to start");
        activeJobId = payload.job.job_id;
        renderResult(payload);
        statusLine.textContent = payload.job.current_message;
        pollTimer = window.setInterval(() => pollJob(activeJobId), 700);
        pollJob(activeJobId);
      }} catch (error) {{
        buildButton.disabled = false;
        statusLine.textContent = error.message;
      }}
    }}

    form.addEventListener("submit", (event) => {{
      event.preventDefault();
      const idea = ideaInput.value.trim();
      if (!idea) {{
        statusLine.textContent = "Enter a product idea before starting the build.";
        return;
      }}
      if (activeJobId) {{
        statusLine.textContent = "A build is already running.";
        return;
      }}
      startBuild(idea);
    }});

    fillButton.addEventListener("click", () => {{
      ideaInput.value = defaultIdea;
      ideaInput.focus();
      statusLine.textContent = "Loaded the competition-style agent prompt.";
    }});

    document.querySelectorAll(".chip").forEach((button) => {{
      button.addEventListener("click", () => {{
        ideaInput.value = button.dataset.idea || "";
        statusLine.textContent = `Loaded sample idea: ${{button.textContent}}`;
      }});
    }});

    renderResult(initialPayload);
  </script>
</body>
</html>
"""


def render_artifact_page(run_id: str, artifact_name: str, content: str) -> str:
    escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{artifact_name} | {run_id}</title>
  <style>
    body {{ margin: 0; padding: 32px 18px; background: #f4efe6; color: #13261d; font-family: "Aptos","Trebuchet MS",sans-serif; }}
    main {{ width: min(960px, 100%); margin: 0 auto; background: rgba(255,250,242,.94); border: 1px solid rgba(19,38,29,.1); border-radius: 24px; box-shadow: 0 24px 60px rgba(20,26,19,.12); overflow: hidden; }}
    header {{ padding: 24px 28px; background: linear-gradient(135deg, rgba(200,95,40,.12), rgba(17,97,73,.1)); border-bottom: 1px solid rgba(19,38,29,.08); }}
    a {{ color: #8f3810; text-decoration: none; font-weight: 700; }}
    pre {{ margin: 0; padding: 28px; overflow-x: auto; white-space: pre-wrap; word-break: break-word; font-family: Consolas,"Courier New",monospace; line-height: 1.5; font-size: .95rem; }}
  </style>
</head>
<body>
  <main>
    <header><a href="/">Back to dashboard</a><h1>{artifact_name}</h1><p>Run: {run_id}</p></header>
    <pre>{escaped}</pre>
  </main>
</body>
</html>
"""
