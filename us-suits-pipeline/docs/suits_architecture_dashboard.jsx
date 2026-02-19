import { useState } from "react";

const C = {
  bg: "#0a0e1a",
  surface: "#111827",
  card: "#1a2236",
  border: "#2a3654",
  borderHi: "#3d5278",
  text: "#e2e8f0",
  textDim: "#7b8ba8",
  textFaint: "#4a5875",
  accent: "#22d3ee",
  accentDim: "#0e7490",
  bronze: "#d97706",
  bronzeBg: "#451a03",
  bronzeSurface: "#78350f",
  silver: "#94a3b8",
  silverBg: "#1e293b",
  silverSurface: "#334155",
  gold: "#eab308",
  goldBg: "#422006",
  goldSurface: "#713f12",
  green: "#34d399",
  greenBg: "#064e3b",
  red: "#f87171",
  redBg: "#7f1d1d",
  purple: "#a78bfa",
  purpleBg: "#2e1065",
};

const tabs = [
  { id: "arch", icon: "◈", label: "Architecture" },
  { id: "flow", icon: "⟶", label: "Data Flow" },
  { id: "schema", icon: "⊞", label: "Schema Map" },
  { id: "dag", icon: "◎", label: "Airflow DAG" },
  { id: "quality", icon: "✦", label: "Quality" },
  { id: "er", icon: "⬡", label: "Entity Model" },
  { id: "tech", icon: "⚙", label: "Tech Stack" },
];

function Badge({ children, color = C.accent, bg = "rgba(34,211,238,0.1)" }) {
  return (
    <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600, color, background: bg, letterSpacing: 0.3 }}>
      {children}
    </span>
  );
}

function Card({ title, icon, accent = C.accent, children, style = {} }) {
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, overflow: "hidden", ...style }}>
      {title && (
        <div style={{ padding: "10px 14px", borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 8 }}>
          {icon && <span style={{ fontSize: 14 }}>{icon}</span>}
          <span style={{ color: accent, fontWeight: 700, fontSize: 13, fontFamily: "'JetBrains Mono', 'Fira Code', monospace" }}>{title}</span>
        </div>
      )}
      <div style={{ padding: 14 }}>{children}</div>
    </div>
  );
}

function LayerBadge({ layer }) {
  const cfg = {
    bronze: { icon: "🥉", color: C.bronze, bg: C.bronzeBg },
    silver: { icon: "🥈", color: C.silver, bg: C.silverBg },
    gold: { icon: "🥇", color: C.gold, bg: C.goldBg },
  }[layer];
  return <Badge color={cfg.color} bg={cfg.bg}>{cfg.icon} {layer.toUpperCase()}</Badge>;
}

/* ═══════════════ ARCHITECTURE OVERVIEW ═══════════════ */
function ArchView() {
  const sources = [
    { code: "TX", county: "Harris", fmt: "CSV (pipe)" },
    { code: "CA", county: "LA", fmt: "JSON" },
    { code: "NY", county: "Kings", fmt: "CSV" },
    { code: "FL", county: "Miami-Dade", fmt: "CSV" },
    { code: "IL", county: "Cook", fmt: "CSV" },
    { code: "OH", county: "Cuyahoga", fmt: "CSV (tab)" },
  ];

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ color: C.text, fontSize: 18, margin: "0 0 6px", fontFamily: "'Playfair Display', Georgia, serif" }}>System Architecture</h2>
        <p style={{ color: C.textDim, fontSize: 12, margin: 0, lineHeight: 1.6 }}>
          End-to-end medallion pipeline ingesting court suit records from 6 US states through Bronze (raw) → Silver (canonical) → Gold (consumer views).
        </p>
      </div>

      {/* Sources */}
      <div style={{ marginBottom: 4 }}>
        <div style={{ color: C.textFaint, fontSize: 9, fontWeight: 700, letterSpacing: 2, marginBottom: 8, textTransform: "uppercase" }}>Data Sources</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 6 }}>
          {sources.map(s => (
            <div key={s.code} style={{ background: "#0c1a3d", border: "1px solid #1e3a6e", borderRadius: 8, padding: "10px 8px", textAlign: "center" }}>
              <div style={{ fontSize: 18, marginBottom: 2 }}>🏛️</div>
              <div style={{ color: "#60a5fa", fontWeight: 800, fontSize: 16, fontFamily: "monospace" }}>{s.code}</div>
              <div style={{ color: C.textDim, fontSize: 9 }}>{s.county} Co.</div>
              <div style={{ color: C.textFaint, fontSize: 8, marginTop: 2 }}>{s.fmt}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Arrow */}
      <div style={{ textAlign: "center", color: C.textFaint, fontSize: 18, margin: "4px 0" }}>▼ ▼ ▼</div>

      {/* Bronze */}
      <div style={{ background: `linear-gradient(135deg, ${C.bronzeBg}, ${C.bronzeSurface})`, border: `1px solid ${C.bronze}33`, borderRadius: 10, padding: 14, marginBottom: 4 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 20 }}>🥉</span>
            <div>
              <div style={{ color: C.bronze, fontWeight: 800, fontSize: 14, fontFamily: "'Playfair Display', Georgia, serif" }}>BRONZE — Raw Ingestion</div>
              <div style={{ color: "#b45309", fontSize: 10 }}>PySpark • Parquet on GCS • Schema-on-Read</div>
            </div>
          </div>
          <Badge color={C.bronze} bg="rgba(217,119,6,0.15)">REQ-BRZ-001→006</Badge>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6 }}>
          {["State-native schemas preserved as strings", "Metadata: _batch_id, _source_state, _ingestion_timestamp", "Partitioned by state_code / ingestion_date"].map((t, i) => (
            <div key={i} style={{ background: "rgba(0,0,0,0.3)", borderRadius: 6, padding: "6px 10px", color: "#fbbf24", fontSize: 10 }}>{t}</div>
          ))}
        </div>
      </div>

      {/* QG1 */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, margin: "4px 0", padding: "0 20px" }}>
        <div style={{ flex: 1, height: 1, background: C.green }}></div>
        <div style={{ background: C.greenBg, border: `1px solid ${C.green}44`, borderRadius: 6, padding: "4px 12px", color: C.green, fontSize: 10, fontWeight: 700, whiteSpace: "nowrap" }}>
          🔍 Quality Gate 1 — null checks, date parsing, state validation (≥95%)
        </div>
        <div style={{ flex: 1, height: 1, background: C.green }}></div>
      </div>

      {/* Silver */}
      <div style={{ background: `linear-gradient(135deg, ${C.silverBg}, ${C.silverSurface})`, border: `1px solid ${C.silver}33`, borderRadius: 10, padding: 14, marginBottom: 4 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 20 }}>🥈</span>
            <div>
              <div style={{ color: C.silver, fontWeight: 800, fontSize: 14, fontFamily: "'Playfair Display', Georgia, serif" }}>SILVER — Canonical Schema</div>
              <div style={{ color: "#64748b", fontSize: 10 }}>Field Mapping • Date Standardization • Type Harmonization • Dedup</div>
            </div>
          </div>
          <Badge color={C.silver} bg="rgba(148,163,184,0.12)">REQ-SLV-001→008</Badge>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6 }}>
          {[
            { name: "silver_suit", desc: "Unified suit record — all states + federal" },
            { name: "silver_suit_party", desc: "Normalized plaintiff/defendant per suit" },
            { name: "silver_suit_docket", desc: "Case events & activity timeline" },
          ].map(t => (
            <div key={t.name} style={{ background: "rgba(0,0,0,0.3)", borderRadius: 6, padding: "6px 10px" }}>
              <div style={{ color: C.accent, fontSize: 11, fontFamily: "monospace", fontWeight: 600 }}>{t.name}</div>
              <div style={{ color: C.textDim, fontSize: 9 }}>{t.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* QG2 */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, margin: "4px 0", padding: "0 20px" }}>
        <div style={{ flex: 1, height: 1, background: C.green }}></div>
        <div style={{ background: C.greenBg, border: `1px solid ${C.green}44`, borderRadius: 6, padding: "4px 12px", color: C.green, fontSize: 10, fontWeight: 700, whiteSpace: "nowrap" }}>
          🔍 Quality Gate 2 — unique IDs, canonical values, referential integrity (≥98%)
        </div>
        <div style={{ flex: 1, height: 1, background: C.green }}></div>
      </div>

      {/* Gold */}
      <div style={{ background: `linear-gradient(135deg, ${C.goldBg}, ${C.goldSurface})`, border: `1px solid ${C.gold}33`, borderRadius: 10, padding: 14, marginBottom: 4 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 20 }}>🥇</span>
            <div>
              <div style={{ color: C.gold, fontWeight: 800, fontSize: 14, fontFamily: "'Playfair Display', Georgia, serif" }}>GOLD — Consumer Best Views</div>
              <div style={{ color: "#a16207", fontSize: 10 }}>BigQuery Tables • Partitioned & Clustered • Materialized Views</div>
            </div>
          </div>
          <Badge color={C.gold} bg="rgba(234,179,8,0.12)">REQ-GLD-001→005</Badge>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 6 }}>
          {[
            { name: "suit_best_view", desc: "1 row/suit + enrichments" },
            { name: "party_best_view", desc: "Cross-suit party metrics" },
            { name: "state_summary", desc: "State × year × type aggs" },
            { name: "monthly_trends", desc: "Rolling averages + YoY" },
          ].map(t => (
            <div key={t.name} style={{ background: "rgba(0,0,0,0.3)", borderRadius: 6, padding: "6px 10px" }}>
              <div style={{ color: C.gold, fontSize: 10, fontFamily: "monospace", fontWeight: 600 }}>gold_{t.name}</div>
              <div style={{ color: "#a16207", fontSize: 9 }}>{t.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Arrow */}
      <div style={{ textAlign: "center", color: C.textFaint, fontSize: 18, margin: "4px 0" }}>▼ ▼ ▼</div>

      {/* Consumers */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 6 }}>
        {[
          { icon: "📊", name: "Looker / Tableau", desc: "BI Dashboards" },
          { icon: "🤖", name: "ML Feature Store", desc: "Risk Models" },
          { icon: "🔍", name: "Search Portal", desc: "Due Diligence" },
          { icon: "⚡", name: "REST API", desc: "Downstream Services" },
        ].map(c => (
          <div key={c.name} style={{ background: C.purpleBg, border: `1px solid ${C.purple}33`, borderRadius: 8, padding: "8px 10px", textAlign: "center" }}>
            <div style={{ fontSize: 16 }}>{c.icon}</div>
            <div style={{ color: C.purple, fontSize: 10, fontWeight: 700 }}>{c.name}</div>
            <div style={{ color: C.textFaint, fontSize: 9 }}>{c.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════ DATA FLOW ═══════════════ */
function FlowView() {
  const states = [
    { code: "TX", fmt: "Pipe CSV ( | )", dateIn: "MM/dd/yyyy", fields: "cause_nbr, case_number, file_date, case_type, case_status, plaintiff_name, defendant_name, judge, amount" },
    { code: "CA", fmt: "Nested JSON", dateIn: "yyyy-MM-dd", fields: "docket_id, case_type_code, filing_date, parties.plaintiffs[], parties.defendants[], court_division, amount_controversy" },
    { code: "NY", fmt: "Comma CSV", dateIn: "MM/dd/yyyy", fields: "index_number, action_type, date_filed, status, plaintiff, defendant, judge_assigned, relief_sought" },
    { code: "FL", fmt: "CSV (no date seps)", dateIn: "yyyyMMdd", fields: "case_id, case_type, filed_dt, case_status, pty_plaintiff, pty_defendant, judge_name, amt_claimed" },
    { code: "IL", fmt: "CSV (month names)", dateIn: "dd-MMM-yyyy", fields: "case_number, case_category, filing_date, case_status, plaintiff_info, defendant_info, presiding_judge" },
    { code: "OH", fmt: "Tab-delimited CSV", dateIn: "M/d/yyyy", fields: "case_num, type_cd, file_dt, status_cd, plaintiff_nm, defendant_nm, judge_nm, claim_amt" },
  ];

  return (
    <div>
      <h2 style={{ color: C.text, fontSize: 18, margin: "0 0 6px", fontFamily: "'Playfair Display', Georgia, serif" }}>Data Flow — State to Canonical</h2>
      <p style={{ color: C.textDim, fontSize: 12, margin: "0 0 16px" }}>
        Each state delivers data in a unique format and schema. The Silver layer maps all to a single canonical model.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 40px 1fr", gap: 0, alignItems: "start" }}>
        {/* Left: Source schemas */}
        <div>
          <div style={{ color: C.textFaint, fontSize: 9, fontWeight: 700, letterSpacing: 2, marginBottom: 8, textTransform: "uppercase" }}>State-Native Schemas (Bronze)</div>
          {states.map(s => (
            <div key={s.code} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: 10, marginBottom: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ color: C.accent, fontWeight: 800, fontSize: 16, fontFamily: "monospace" }}>{s.code}</span>
                  <Badge color={C.bronze} bg={C.bronzeBg}>{s.fmt}</Badge>
                </div>
                <span style={{ color: C.textFaint, fontSize: 9, fontFamily: "monospace" }}>date: {s.dateIn}</span>
              </div>
              <div style={{ color: C.textDim, fontSize: 9, fontFamily: "monospace", lineHeight: 1.5, wordBreak: "break-all" }}>{s.fields}</div>
            </div>
          ))}
        </div>

        {/* Center arrow */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", paddingTop: 60 }}>
          <div style={{ writingMode: "vertical-rl", textOrientation: "mixed", color: C.textFaint, fontSize: 9, fontWeight: 600, letterSpacing: 1, marginBottom: 8 }}>PYSPARK TRANSFORM</div>
          <div style={{ width: 2, height: 40, background: `linear-gradient(to bottom, ${C.bronze}, ${C.silver})` }}></div>
          <div style={{ color: C.accent, fontSize: 20, margin: "4px 0" }}>⟶</div>
          <div style={{ width: 2, height: 40, background: `linear-gradient(to bottom, ${C.silver}, ${C.gold})` }}></div>
        </div>

        {/* Right: Canonical schema */}
        <div>
          <div style={{ color: C.textFaint, fontSize: 9, fontWeight: 700, letterSpacing: 2, marginBottom: 8, textTransform: "uppercase" }}>Canonical Schema (Silver)</div>
          <Card title="silver_suit" icon="📋" accent={C.accent}>
            {[
              { f: "suit_id", t: "STRING", n: "PK — {state}_{county}_{case_number}", pk: true },
              { f: "state_code", t: "STRING(2)", n: "Two-letter code" },
              { f: "county", t: "STRING", n: "Normalized county name" },
              { f: "case_number", t: "STRING", n: "State-native number" },
              { f: "case_type", t: "STRING", n: "→ 10 canonical types" },
              { f: "case_type_raw", t: "STRING", n: "Original code preserved" },
              { f: "filing_date", t: "DATE", n: "→ ISO 8601" },
              { f: "case_status", t: "STRING", n: "→ 8 canonical statuses" },
              { f: "judge_name", t: "STRING", n: "Title Case normalized" },
              { f: "plaintiff_name", t: "STRING", n: "Trimmed, normalized" },
              { f: "defendant_name", t: "STRING", n: "Trimmed, normalized" },
              { f: "amount_demanded", t: "DECIMAL(18,2)", n: "Parsed, cleaned" },
              { f: "disposition", t: "STRING", n: "Settlement / Judgment / …" },
              { f: "disposition_date", t: "DATE", n: "ISO 8601" },
            ].map(r => (
              <div key={r.f} style={{ display: "flex", alignItems: "center", gap: 6, padding: "3px 0", borderBottom: `1px solid ${C.border}22` }}>
                {r.pk && <span style={{ color: C.gold, fontSize: 8 }}>PK</span>}
                <code style={{ color: r.pk ? C.gold : C.accent, fontSize: 11, minWidth: 130 }}>{r.f}</code>
                <span style={{ color: C.textFaint, fontSize: 9, minWidth: 80 }}>{r.t}</span>
                <span style={{ color: C.textDim, fontSize: 9 }}>{r.n}</span>
              </div>
            ))}
          </Card>

          <div style={{ marginTop: 8 }}>
            <Card title="silver_suit_party" icon="👤" accent={C.green}>
              {[
                { f: "party_id", t: "STRING", n: "PK" },
                { f: "suit_id", t: "STRING", n: "FK → silver_suit" },
                { f: "party_type", t: "STRING", n: "PLAINTIFF / DEFENDANT" },
                { f: "party_name", t: "STRING", n: "Normalized name" },
                { f: "is_entity", t: "BOOLEAN", n: "LLC/Inc/Corp detection" },
              ].map(r => (
                <div key={r.f} style={{ display: "flex", alignItems: "center", gap: 6, padding: "2px 0" }}>
                  <code style={{ color: C.green, fontSize: 10, minWidth: 100 }}>{r.f}</code>
                  <span style={{ color: C.textFaint, fontSize: 9, minWidth: 60 }}>{r.t}</span>
                  <span style={{ color: C.textDim, fontSize: 9 }}>{r.n}</span>
                </div>
              ))}
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════ SCHEMA MAPPING ═══════════════ */
function SchemaView() {
  const typeMap = [
    { canonical: "CIVIL", TX: "CV", CA: "CIV", NY: "Civil", FL: "CA", IL: "L", OH: "CV" },
    { canonical: "FAMILY", TX: "FM", CA: "FAM", NY: "Matrimonial", FL: "DR", IL: "D", OH: "DR" },
    { canonical: "CRIMINAL", TX: "CR", CA: "CRIM", NY: "Criminal", FL: "CF/MM", IL: "CR", OH: "CR" },
    { canonical: "PROBATE", TX: "PR", CA: "PROB", NY: "Surrogate", FL: "CP", IL: "P", OH: "PB" },
    { canonical: "SMALL_CLAIMS", TX: "SC", CA: "SC", NY: "Small Claims", FL: "SC", IL: "SC", OH: "SC" },
    { canonical: "EVICTION", TX: "EV", CA: "UD", NY: "L&T", FL: "CC", IL: "EV", OH: "FED" },
    { canonical: "PERSONAL_INJURY", TX: "PI", CA: "PI", NY: "Tort", FL: "—", IL: "L-PI", OH: "—" },
    { canonical: "CONTRACT", TX: "CT", CA: "CT", NY: "Contract", FL: "—", IL: "L-CT", OH: "—" },
    { canonical: "REAL_PROPERTY", TX: "RP", CA: "RE", NY: "Real Prop", FL: "—", IL: "CH", OH: "—" },
    { canonical: "OTHER", TX: "*", CA: "*", NY: "*", FL: "*", IL: "*", OH: "*" },
  ];
  const statusMap = [
    { canonical: "OPEN", TX: "PEND", CA: "Active", NY: "Active", FL: "OPEN", IL: "Open", OH: "ACTIVE" },
    { canonical: "DISPOSED", TX: "DISP", CA: "Disposed", NY: "Disposed", FL: "CLOSED", IL: "Closed", OH: "TERMINATED" },
    { canonical: "DISMISSED", TX: "DISM", CA: "Dismissed", NY: "Dismissed", FL: "—", IL: "Dismissed", OH: "DISMISSED" },
    { canonical: "TRANSFERRED", TX: "TRANSF", CA: "Transferred", NY: "—", FL: "—", IL: "—", OH: "TRANSFERRED" },
    { canonical: "APPEALED", TX: "APPEAL", CA: "—", NY: "—", FL: "—", IL: "—", OH: "—" },
    { canonical: "STAYED", TX: "—", CA: "—", NY: "—", FL: "—", IL: "Continued", OH: "—" },
    { canonical: "SEALED", TX: "—", CA: "—", NY: "—", FL: "—", IL: "—", OH: "—" },
    { canonical: "UNKNOWN", TX: "fallback", CA: "fallback", NY: "fallback", FL: "fallback", IL: "fallback", OH: "fallback" },
  ];

  function MappingTable({ title, spec, data, headerColor }) {
    const stCols = ["TX", "CA", "NY", "FL", "IL", "OH"];
    return (
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <h3 style={{ color: C.text, fontSize: 14, margin: 0, fontFamily: "'Playfair Display', Georgia, serif" }}>{title}</h3>
          <Badge>{spec}</Badge>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, fontSize: 11 }}>
            <thead>
              <tr>
                <th style={{ padding: "8px 10px", background: C.surface, color: headerColor, textAlign: "left", borderBottom: `2px solid ${headerColor}44`, borderRadius: "6px 0 0 0", position: "sticky", left: 0 }}>Canonical</th>
                {stCols.map((s, i) => (
                  <th key={s} style={{ padding: "8px 10px", background: C.surface, color: C.textDim, textAlign: "center", borderBottom: `2px solid ${C.border}`, borderRadius: i === 5 ? "0 6px 0 0" : 0 }}>{s}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i}>
                  <td style={{ padding: "6px 10px", color: headerColor, fontWeight: 700, fontFamily: "monospace", background: i % 2 ? "transparent" : "rgba(0,0,0,0.15)", borderBottom: `1px solid ${C.border}22`, position: "sticky", left: 0 }}>
                    {row.canonical}
                  </td>
                  {stCols.map(s => (
                    <td key={s} style={{ padding: "6px 10px", textAlign: "center", fontFamily: "monospace", fontSize: 10, background: i % 2 ? "transparent" : "rgba(0,0,0,0.15)", borderBottom: `1px solid ${C.border}22`, color: row[s] === "—" || row[s] === "*" || row[s] === "fallback" ? C.textFaint : C.textDim }}>
                      {row[s]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 style={{ color: C.text, fontSize: 18, margin: "0 0 6px", fontFamily: "'Playfair Display', Georgia, serif" }}>Schema Mapping — State → Canonical</h2>
      <p style={{ color: C.textDim, fontSize: 12, margin: "0 0 16px" }}>
        The Silver layer harmonizes ~200 state-specific codes into canonical taxonomies. These mapping tables are the core of <code style={{ color: C.accent }}>src/schemas/state_mappings.py</code>.
      </p>
      <MappingTable title="Case Type Harmonization" spec="REQ-SLV-003" data={typeMap} headerColor={C.gold} />
      <MappingTable title="Status Harmonization" spec="REQ-SLV-004" data={statusMap} headerColor={C.green} />

      <h3 style={{ color: C.text, fontSize: 14, margin: "0 0 10px", fontFamily: "'Playfair Display', Georgia, serif" }}>Date Parsing — 6 Formats → ISO 8601</h3>
      <Badge>REQ-SLV-006</Badge>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6, marginTop: 10 }}>
        {[
          { st: "TX", fmt: "MM/dd/yyyy", ex: "01/15/2025", note: "Standard US format" },
          { st: "CA", fmt: "yyyy-MM-dd", ex: "2025-01-15", note: "Already ISO — passthrough" },
          { st: "NY", fmt: "MM/dd/yyyy", ex: "01/15/2025", note: "Standard US format" },
          { st: "FL", fmt: "yyyyMMdd", ex: "20250115", note: "No separators at all" },
          { st: "IL", fmt: "dd-MMM-yyyy", ex: "15-Jan-2025", note: "Abbreviated month names" },
          { st: "OH", fmt: "M/d/yyyy", ex: "1/15/2025", note: "Variable-width digits" },
        ].map(d => (
          <div key={d.st} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, padding: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ color: C.accent, fontWeight: 800, fontFamily: "monospace" }}>{d.st}</span>
              <code style={{ color: C.bronze, fontSize: 10 }}>{d.fmt}</code>
            </div>
            <div style={{ color: C.textDim, fontSize: 11, fontFamily: "monospace" }}>
              <span style={{ color: C.textFaint }}>{d.ex}</span>
              <span style={{ color: C.green, margin: "0 6px" }}>→</span>
              <span style={{ color: C.green }}>2025-01-15</span>
            </div>
            <div style={{ color: C.textFaint, fontSize: 9, marginTop: 3 }}>{d.note}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════ AIRFLOW DAG ═══════════════ */
function DagView() {
  const stages = [
    { label: "START", color: C.textFaint, tasks: [{ name: "start", w: 1 }] },
    {
      label: "BRONZE — Parallel State Ingestion", color: C.bronze,
      tasks: [
        { name: "ingest_tx_suits", w: 1 }, { name: "ingest_ca_suits", w: 1 },
        { name: "ingest_ny_suits", w: 1 }, { name: "ingest_fl_suits", w: 1 },
        { name: "ingest_il_suits", w: 1 }, { name: "ingest_oh_suits", w: 1 },
      ]
    },
    { label: "QUALITY GATE 1", color: C.green, tasks: [{ name: "bronze_quality_gate", w: 3 }] },
    { label: "SILVER — Canonicalize", color: C.silver, tasks: [{ name: "silver_canonicalize_all_states", w: 3 }] },
    { label: "QUALITY GATE 2", color: C.green, tasks: [{ name: "silver_quality_gate", w: 3 }] },
    {
      label: "GOLD — Build Consumer Views", color: C.gold,
      tasks: [
        { name: "gold_suit_best_view", w: 1 }, { name: "gold_party_best_view", w: 1 }, { name: "gold_analytics", w: 1 },
      ]
    },
    { label: "BIGQUERY LOAD", color: C.accent, tasks: [{ name: "bq_load_all_gold_tables", w: 3 }] },
    { label: "END", color: C.textFaint, tasks: [{ name: "notify_completion ✓", w: 1 }] },
  ];

  return (
    <div>
      <h2 style={{ color: C.text, fontSize: 18, margin: "0 0 6px", fontFamily: "'Playfair Display', Georgia, serif" }}>Airflow DAG — suits_medallion_pipeline</h2>
      <div style={{ display: "flex", gap: 20 }}>
        {/* DAG visual */}
        <div style={{ flex: 2 }}>
          {stages.map((stage, si) => (
            <div key={si}>
              <div style={{ color: stage.color, fontSize: 9, fontWeight: 700, letterSpacing: 1.5, marginBottom: 4, marginTop: si === 0 ? 0 : 2, opacity: 0.7 }}>
                {stage.label}
              </div>
              <div style={{ display: "flex", gap: 4, marginBottom: 2 }}>
                {stage.tasks.map((t, ti) => (
                  <div key={ti} style={{
                    flex: t.w,
                    background: C.card,
                    border: `1px solid ${stage.color}44`,
                    borderLeft: `3px solid ${stage.color}`,
                    borderRadius: 6,
                    padding: "7px 10px",
                    color: stage.color,
                    fontSize: 10,
                    fontFamily: "monospace",
                    fontWeight: 600,
                  }}>
                    {t.name}
                  </div>
                ))}
              </div>
              {si < stages.length - 1 && (
                <div style={{ textAlign: "center", color: C.textFaint, fontSize: 12, margin: "1px 0" }}>│</div>
              )}
            </div>
          ))}
        </div>

        {/* Config panel */}
        <div style={{ flex: 1 }}>
          <Card title="DAG Config" icon="⚙" accent={C.accent}>
            {[
              { k: "dag_id", v: "suits_medallion_pipeline" },
              { k: "schedule", v: "@daily (06:00 UTC)" },
              { k: "retries", v: "2 (exponential backoff)" },
              { k: "max_active_runs", v: "1" },
              { k: "catchup", v: "False" },
              { k: "tags", v: "suits, medallion, pyspark" },
            ].map(r => (
              <div key={r.k} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: `1px solid ${C.border}22` }}>
                <span style={{ color: C.textDim, fontSize: 10 }}>{r.k}</span>
                <code style={{ color: C.accent, fontSize: 10 }}>{r.v}</code>
              </div>
            ))}
          </Card>

          <div style={{ marginTop: 10 }}>
            <Card title="Task Details" icon="📝" accent={C.gold}>
              <div style={{ color: C.textDim, fontSize: 10, lineHeight: 1.7 }}>
                <p style={{ margin: "0 0 8px" }}><strong style={{ color: C.bronze }}>Bronze:</strong> 6 parallel PythonOperator tasks. Each reads state-native format, appends metadata, writes Parquet to GCS.</p>
                <p style={{ margin: "0 0 8px" }}><strong style={{ color: C.green }}>Quality Gates:</strong> PythonOperators running PySpark checks. FAIL status raises RuntimeError, blocking downstream.</p>
                <p style={{ margin: "0 0 8px" }}><strong style={{ color: C.silver }}>Silver:</strong> Single PythonOperator processing all states. Field mapping, date parsing, dedup, quarantine.</p>
                <p style={{ margin: "0 0 8px" }}><strong style={{ color: C.gold }}>Gold:</strong> 3 parallel tasks building suit_best_view, party_best_view, and analytics aggregates.</p>
                <p style={{ margin: 0 }}><strong style={{ color: C.accent }}>BigQuery:</strong> BigQueryInsertJobOperator loads Parquet from GCS with WRITE_TRUNCATE + partitioning.</p>
              </div>
            </Card>
          </div>

          <div style={{ marginTop: 10 }}>
            <Card title="SLA & Alerts" icon="🔔" accent={C.red}>
              <div style={{ color: C.textDim, fontSize: 10, lineHeight: 1.7 }}>
                <p style={{ margin: "0 0 4px" }}>Gold refresh ≤ <strong style={{ color: C.gold }}>4 hours</strong> after Bronze ingest</p>
                <p style={{ margin: "0 0 4px" }}>Staleness alert if Gold &gt; <strong style={{ color: C.red }}>8 hours</strong> behind</p>
                <p style={{ margin: 0 }}>Quality gate failure → <strong style={{ color: C.red }}>Slack + PagerDuty</strong></p>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════ QUALITY FRAMEWORK ═══════════════ */
function QualityView() {
  const gates = [
    {
      name: "Bronze → Silver Gate", threshold: "95%", color: C.bronze, spec: "REQ-DQ-001",
      checks: [
        { name: "not_null(case_number)", sev: "BLOCK", desc: "Case/docket number present" },
        { name: "not_null(filing_date)", sev: "BLOCK", desc: "Filing date present" },
        { name: "not_null(plaintiff)", sev: "WARN", desc: "At least one plaintiff name" },
        { name: "valid_state_code", sev: "BLOCK", desc: "State in [TX,CA,NY,FL,IL,OH]" },
        { name: "parseable_date", sev: "BLOCK", desc: "Date can be parsed per state format" },
        { name: "non_negative_amount", sev: "WARN", desc: "Amount ≥ 0 where present" },
      ]
    },
    {
      name: "Silver → Gold Gate", threshold: "98%", color: C.silver, spec: "REQ-DQ-002",
      checks: [
        { name: "unique(suit_id)", sev: "BLOCK", desc: "Globally unique suit identifier" },
        { name: "accepted_values(case_type)", sev: "BLOCK", desc: "In canonical taxonomy (10 values)" },
        { name: "accepted_values(case_status)", sev: "BLOCK", desc: "In canonical status list (8 values)" },
        { name: "valid_date(filing_date)", sev: "BLOCK", desc: "Valid DATE, not future" },
        { name: "party_exists_per_suit", sev: "WARN", desc: "At least one party record per suit" },
      ]
    },
    {
      name: "Gold Output Validation", threshold: "99%", color: C.gold, spec: "REQ-DQ-003",
      checks: [
        { name: "unique(suit_id)", sev: "BLOCK", desc: "Unique in best view" },
        { name: "not_null(primary_plaintiff)", sev: "WARN", desc: "Primary plaintiff populated" },
        { name: "non_negative(days_open)", sev: "BLOCK", desc: "days_open ≥ 0" },
        { name: "valid_state_code", sev: "BLOCK", desc: "State code is valid" },
      ]
    },
  ];

  return (
    <div>
      <h2 style={{ color: C.text, fontSize: 18, margin: "0 0 6px", fontFamily: "'Playfair Display', Georgia, serif" }}>Data Quality Framework</h2>
      <p style={{ color: C.textDim, fontSize: 12, margin: "0 0 16px" }}>
        Quality gates at every layer boundary. Failures quarantine records; blocks halt pipeline progression.
      </p>

      {gates.map(gate => (
        <div key={gate.name} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, marginBottom: 12, overflow: "hidden" }}>
          <div style={{ background: C.surface, padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: `1px solid ${C.border}` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ color: gate.color, fontWeight: 800, fontSize: 13 }}>{gate.name}</span>
              <Badge>{gate.spec}</Badge>
            </div>
            <div style={{ background: C.greenBg, border: `1px solid ${C.green}33`, borderRadius: 20, padding: "2px 10px" }}>
              <span style={{ color: C.green, fontSize: 11, fontWeight: 700 }}>Threshold: {gate.threshold}</span>
            </div>
          </div>
          <div style={{ padding: "6px 14px" }}>
            {gate.checks.map(c => (
              <div key={c.name} style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 0", borderBottom: `1px solid ${C.border}22` }}>
                <span style={{
                  fontSize: 9, fontWeight: 800, padding: "2px 6px", borderRadius: 3, minWidth: 42, textAlign: "center",
                  color: c.sev === "BLOCK" ? C.red : C.gold,
                  background: c.sev === "BLOCK" ? C.redBg : C.goldBg,
                }}>{c.sev}</span>
                <code style={{ color: C.accent, fontSize: 10, minWidth: 200, fontWeight: 600 }}>{c.name}</code>
                <span style={{ color: C.textDim, fontSize: 10 }}>{c.desc}</span>
              </div>
            ))}
          </div>
        </div>
      ))}

      <Card title="🚫 Quarantine Pipeline" icon="" accent={C.red} style={{ background: C.redBg, borderColor: `${C.red}33` }}>
        <div style={{ color: "#fca5a5", fontSize: 11, lineHeight: 1.7 }}>
          <div style={{ marginBottom: 6 }}>Failed records stored at: <code style={{ color: "#fecaca" }}>gs://bucket/quarantine/{"{layer}"}/{"{table}"}/{"{date}"}/*.parquet</code></div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8 }}>
            {[
              "Each record includes: original data + failure reason + check name",
              "Weekly quarantine volume report by failure type per state",
              "Spike alert if quarantine volume > 2× rolling 7-day average",
              "Reconciliation: Bronze count − Silver count = quarantine + dedup",
            ].map((t, i) => (
              <div key={i} style={{ background: "rgba(0,0,0,0.2)", borderRadius: 6, padding: "6px 8px", fontSize: 10, color: "#fca5a5" }}>• {t}</div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
}

/* ═══════════════ ENTITY MODEL ═══════════════ */
function ERView() {
  const entities = [
    {
      name: "silver_suit", color: C.accent, x: "25%", y: 30,
      fields: ["suit_id (PK)", "state_code", "county", "case_number", "case_type", "filing_date", "case_status", "judge_name", "amount_demanded"]
    },
    {
      name: "silver_suit_party", color: C.green, x: "70%", y: 30,
      fields: ["party_id (PK)", "suit_id (FK)", "party_type", "party_name", "is_entity"]
    },
    {
      name: "gold_suit_best_view", color: C.gold, x: "10%", y: 300,
      fields: ["suit_id (PK)", "year_filed", "days_open", "primary_plaintiff", "primary_defendant", "plaintiff_count"]
    },
    {
      name: "gold_party_best_view", color: C.gold, x: "45%", y: 300,
      fields: ["party_name", "total_suits_as_plaintiff", "total_suits_as_defendant", "is_frequent_litigant"]
    },
    {
      name: "gold_state_summary", color: C.gold, x: "78%", y: 300,
      fields: ["state × year × type", "suit_count", "avg_days_to_disposition", "disposition_rate"]
    },
  ];

  return (
    <div>
      <h2 style={{ color: C.text, fontSize: 18, margin: "0 0 6px", fontFamily: "'Playfair Display', Georgia, serif" }}>Entity Relationship Model</h2>
      <p style={{ color: C.textDim, fontSize: 12, margin: "0 0 16px" }}>Silver canonical tables feed Gold consumer views through PySpark aggregation and enrichment.</p>

      <div style={{ position: "relative", minHeight: 500 }}>
        {/* Silver layer label */}
        <div style={{ position: "absolute", top: 6, left: 0, color: C.silver, fontSize: 9, fontWeight: 700, letterSpacing: 2 }}>SILVER LAYER</div>
        <div style={{ position: "absolute", top: 275, left: 0, color: C.gold, fontSize: 9, fontWeight: 700, letterSpacing: 2 }}>GOLD LAYER</div>

        {/* Relationship lines */}
        <svg style={{ position: "absolute", top: 0, left: 0, width: "100%", height: 500, pointerEvents: "none" }}>
          {/* suit → party (1:N) */}
          <line x1="42%" y1="170" x2="62%" y2="50" stroke={C.green} strokeWidth={1.5} strokeDasharray="6,3" opacity={0.5} />
          <text x="54%" y="105" fill={C.green} fontSize="10" textAnchor="middle" fontWeight="600">1 : N</text>
          {/* suit → gold_suit_best_view (1:1) */}
          <line x1="25%" y1="190" x2="20%" y2="300" stroke={C.gold} strokeWidth={1.5} strokeDasharray="6,3" opacity={0.4} />
          <text x="18%" y="250" fill={C.gold} fontSize="9" textAnchor="middle">enrich</text>
          {/* party → gold_party_best_view */}
          <line x1="70%" y1="170" x2="58%" y2="300" stroke={C.gold} strokeWidth={1.5} strokeDasharray="6,3" opacity={0.4} />
          <text x="67%" y="240" fill={C.gold} fontSize="9" textAnchor="middle">aggregate</text>
          {/* suit → gold_state_summary */}
          <line x1="35%" y1="190" x2="85%" y2="300" stroke={C.gold} strokeWidth={1.5} strokeDasharray="6,3" opacity={0.4} />
        </svg>

        {/* Entity cards */}
        {entities.map(e => (
          <div key={e.name} style={{
            position: "absolute", left: e.x, top: e.y, transform: "translateX(-50%)",
            background: C.card, border: `1px solid ${e.color}44`, borderTop: `3px solid ${e.color}`,
            borderRadius: 8, padding: 0, minWidth: 180, maxWidth: 220, zIndex: 1,
          }}>
            <div style={{ padding: "8px 10px", borderBottom: `1px solid ${C.border}`, color: e.color, fontWeight: 800, fontSize: 12, fontFamily: "monospace" }}>
              {e.name}
            </div>
            <div style={{ padding: "6px 10px" }}>
              {e.fields.map(f => (
                <div key={f} style={{
                  fontSize: 10, fontFamily: "monospace", padding: "2px 0",
                  color: f.includes("PK") ? C.gold : f.includes("FK") ? C.green : C.textDim,
                  fontWeight: f.includes("PK") ? 700 : 400,
                }}>{f}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════ TECH STACK ═══════════════ */
function TechView() {
  const stack = [
    { layer: "Processing", tech: "PySpark 3.5+ on Dataproc", icon: "⚡", color: C.accent, desc: "Distributed transforms across all layers. Handles 100M+ records. Native Parquet/GCS/BigQuery connectors. State-level parallelism.", files: ["src/bronze/ingest.py", "src/silver/canonicalize.py", "src/gold/build_best_view.py"] },
    { layer: "Storage", tech: "Parquet on Google Cloud Storage", icon: "💾", color: C.silver, desc: "Columnar, Snappy-compressed. Schema evolution support. Partitioned by state_code/ingestion_date. Backs BigQuery external tables.", files: ["gs://bucket/bronze/suits/", "gs://bucket/silver/suits/", "gs://bucket/gold/suits/"] },
    { layer: "Warehouse", tech: "BigQuery", icon: "🏢", color: C.gold, desc: "Sub-second analytical queries on Gold. Partitioned by filing_date (MONTH), clustered by state_code + case_type. Feeds BI tools directly.", files: ["bigquery/ddl/create_gold_tables.sql", "bigquery/views/v_suit_search.sql", "bigquery/views/v_state_dashboard.sql"] },
    { layer: "Orchestration", tech: "Apache Airflow (Cloud Composer)", icon: "🔄", color: C.green, desc: "Complex DAG dependencies across 6 states. Quality gates between layers. SLA monitoring. Retry with exponential backoff.", files: ["airflow/dags/suits_medallion_pipeline.py"] },
    { layer: "Data Quality", tech: "Custom Framework + Great Expectations", icon: "✅", color: "#f472b6", desc: "PySpark-native quality checks. Threshold-based pass/fail/warn. Quarantine pipeline for invalid records.", files: ["src/quality/spark_checks.py"] },
    { layer: "Specifications", tech: "OpenSpec", icon: "📋", color: C.purple, desc: "Living specs (REQ-BRZ-*, REQ-SLV-*, REQ-GLD-*, REQ-DQ-*). Spec-driven development: human reviews spec before agent writes code.", files: ["openspec/specs/bronze-state-ingestion/spec.md", "openspec/specs/silver-canonical-suits/spec.md", "openspec/specs/gold-best-view/spec.md"] },
    { layer: "Testing", tech: "pytest + chispa (PySpark testing)", icon: "🧪", color: "#fb923c", desc: "Unit tests for state mappings and business logic. Integration tests running full Bronze → Silver → Gold. Minimum 80% coverage.", files: ["tests/unit/test_state_mappings.py", "tests/integration/test_pipeline_e2e.py"] },
    { layer: "CI/CD", tech: "GitHub Actions", icon: "🚀", color: "#60a5fa", desc: "Lint (ruff) → Unit tests → Integration tests → Pipeline smoke test. Java 17 setup for local PySpark.", files: [".github/workflows/ci.yml"] },
  ];

  return (
    <div>
      <h2 style={{ color: C.text, fontSize: 18, margin: "0 0 6px", fontFamily: "'Playfair Display', Georgia, serif" }}>Technology Stack</h2>
      <p style={{ color: C.textDim, fontSize: 12, margin: "0 0 16px" }}>Every component chosen for a specific reason. This is the rationale behind each technology decision.</p>
      <div style={{ display: "grid", gap: 8 }}>
        {stack.map(s => (
          <div key={s.layer} style={{ background: C.card, border: `1px solid ${C.border}`, borderLeft: `3px solid ${s.color}`, borderRadius: 8, padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 18 }}>{s.icon}</span>
                <div>
                  <div style={{ color: s.color, fontWeight: 800, fontSize: 13 }}>{s.layer}</div>
                  <div style={{ color: C.text, fontSize: 11, fontWeight: 600 }}>{s.tech}</div>
                </div>
              </div>
            </div>
            <div style={{ color: C.textDim, fontSize: 11, lineHeight: 1.5, marginBottom: 6 }}>{s.desc}</div>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {s.files.map(f => (
                <code key={f} style={{ fontSize: 9, color: C.textFaint, background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: 3 }}>{f}</code>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════ MAIN APP ═══════════════ */
export default function App() {
  const [activeTab, setActiveTab] = useState("arch");

  const views = {
    arch: ArchView, flow: FlowView, schema: SchemaView,
    dag: DagView, quality: QualityView, er: ERView, tech: TechView,
  };
  const ActiveView = views[activeTab];

  return (
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: "'IBM Plex Sans', -apple-system, sans-serif", color: C.text }}>
      <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=IBM+Plex+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet" />

      <div style={{ maxWidth: 980, margin: "0 auto", padding: "20px 16px" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 42, height: 42, borderRadius: 10, background: `linear-gradient(135deg, ${C.bronze}, ${C.gold})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22 }}>🏛️</div>
            <div>
              <h1 style={{ fontSize: 22, margin: 0, fontWeight: 700, fontFamily: "'Playfair Display', Georgia, serif", letterSpacing: -0.5 }}>
                US Suits Pipeline
              </h1>
              <div style={{ color: C.textDim, fontSize: 11, marginTop: 2, display: "flex", gap: 6, flexWrap: "wrap" }}>
                <Badge>PySpark</Badge> <Badge>BigQuery</Badge> <Badge>Airflow</Badge> <Badge color={C.gold} bg={C.goldBg}>Medallion</Badge> <Badge color={C.purple} bg={C.purpleBg}>OpenSpec</Badge>
              </div>
            </div>
          </div>
          <div style={{ color: C.textFaint, fontSize: 10, textAlign: "right" }}>
            <div>6 States • 3 Layers • 500+ records/state</div>
            <div>Spec-Driven AI Development</div>
          </div>
        </div>

        {/* Tab bar */}
        <div style={{ display: "flex", gap: 2, marginBottom: 16, background: C.surface, borderRadius: 10, padding: 3, flexWrap: "wrap" }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              flex: 1, minWidth: 100, padding: "8px 6px", borderRadius: 8, border: "none", cursor: "pointer",
              fontSize: 11, fontWeight: 700, transition: "all 0.2s ease", fontFamily: "'IBM Plex Sans', sans-serif",
              background: activeTab === t.id ? C.accent : "transparent",
              color: activeTab === t.id ? C.bg : C.textDim,
            }}>
              <span style={{ marginRight: 4 }}>{t.icon}</span>{t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <ActiveView />
        </div>

        {/* Footer */}
        <div style={{ textAlign: "center", color: C.textFaint, fontSize: 9, marginTop: 16, letterSpacing: 1 }}>
          US PUBLIC RECORDS — SPEC-DRIVEN MEDALLION ARCHITECTURE — PYSPARK + BIGQUERY + AIRFLOW
        </div>
      </div>
    </div>
  );
}
