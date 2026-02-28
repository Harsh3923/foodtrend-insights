import { useEffect, useMemo, useState } from "react";
import ScoresHistogram from "./ScoresHistogram";

const API_BASE = "http://127.0.0.1:8000"; // Django base

const ORIGIN_LABEL = {
  other: "Other/Unclear",
  american_canadian: "American/Canadian",
  italian: "Italian",
  mexican: "Mexican",
  korean: "Korean",
  japanese: "Japanese",
  chinese: "Chinese",
  indian: "Indian",
  middle_eastern: "Middle Eastern",
  southeast_asian: "Southeast Asian",
  french: "French",
  fusion: "Fusion",
};

function timeAgo(iso) {
  const d = new Date(iso);
  const s = Math.floor((Date.now() - d.getTime()) / 1000);
  if (Number.isNaN(s)) return "";
  const mins = Math.floor(s / 60);
  const hrs = Math.floor(mins / 60);
  const days = Math.floor(hrs / 24);
  if (days > 0) return `${days}d ago`;
  if (hrs > 0) return `${hrs}h ago`;
  if (mins > 0) return `${mins}m ago`;
  return "just now";
}

export default function App() {
  const [days, setDays] = useState(7);
  const [limit, setLimit] = useState(20);

  const [trending, setTrending] = useState([]);
  const [trendLoading, setTrendLoading] = useState(false);
  const [trendErr, setTrendErr] = useState("");

  // NEW: cuisines (globalization)
  const [cuisines, setCuisines] = useState([]);
  const [cuisineLoading, setCuisineLoading] = useState(false);
  const [cuisineErr, setCuisineErr] = useState("");

  const [q, setQ] = useState("");
  const [activeTerm, setActiveTerm] = useState("");
  const [results, setResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchErr, setSearchErr] = useState("");

  const top5 = useMemo(() => trending.slice(0, 5), [trending]);

  async function fetchTrending() {
    setTrendLoading(true);
    setTrendErr("");
    try {
      const r = await fetch(`${API_BASE}/api/trends/?days=${days}&limit=${limit}`);
      const data = await r.json();
      setTrending(data.results || []);
    } catch (e) {
      setTrendErr("Failed to load trends. Is Django running on 8000?");
    } finally {
      setTrendLoading(false);
    }
  }

  // NEW: fetch cuisines
  async function fetchCuisines() {
    setCuisineLoading(true);
    setCuisineErr("");
    try {
      const r = await fetch(`${API_BASE}/api/trending-cuisines?days=${days}&limit=12`);
      const data = await r.json();
      setCuisines(data.results || []);
    } catch (e) {
      setCuisineErr("Failed to load cuisines. Is Django running on 8000?");
    } finally {
      setCuisineLoading(false);
    }
  }

  // Refresh both at once
  function refreshAll() {
    fetchTrending();
    fetchCuisines();
  }

  async function runSearch(nextQ, nextTerm) {
    const query = (nextQ ?? q).trim();
    const term = (nextTerm ?? activeTerm).trim();
    if (!query) {
      setResults([]);
      setSearchErr("Type something to search (e.g., ramen, chicken, air fryer).");
      return;
    }

    setSearchLoading(true);
    setSearchErr("");
    try {
      const url =
        `${API_BASE}/api/search/?q=${encodeURIComponent(query)}&days=30&limit=30` +
        (term ? `&term=${encodeURIComponent(term)}` : "");
      const r = await fetch(url);
      const data = await r.json();
      if (!r.ok) {
        setResults([]);
        setSearchErr(data?.error || "Search failed.");
      } else {
        setResults(data.results || []);
      }
    } catch (e) {
      setSearchErr("Failed to search. Check backend + CORS settings.");
    } finally {
      setSearchLoading(false);
    }
  }

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days, limit]);

  function onChip(term) {
    // clicking a term chip sets both search query + term filter
    setQ(term);
    setActiveTerm(term);
    runSearch(term, term);
  }

  return (
    <div style={styles.page}>
      <div style={styles.shell}>
        <header style={styles.header}>
          <div>
            <div style={styles.title}>FoodTrend Insights</div>
            <div style={styles.subtitle}>
              Minimal trend dashboard powered by your Django pipeline (Reddit → terms → trends).
            </div>
          </div>

          <div style={styles.controls}>
            <label style={styles.label}>
              Days
              <input
                type="number"
                min={1}
                max={60}
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                style={styles.inputSmall}
              />
            </label>

            <label style={styles.label}>
              Trend limit
              <input
                type="number"
                min={5}
                max={50}
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                style={styles.inputSmall}
              />
            </label>

            <button onClick={refreshAll} style={styles.btn}>
              Refresh
            </button>
          </div>
        </header>

        <main style={styles.grid}>
          {/* Left: Search */}
          <section style={styles.card}>
            <div style={styles.cardTitle}>Search Posts</div>
            <div style={styles.row}>
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search (e.g., ramen, chicken, air fryer)"
                style={styles.input}
              />
              <button onClick={() => runSearch()} style={styles.btnPrimary}>
                {searchLoading ? "Searching..." : "Search"}
              </button>
            </div>

            <div style={styles.row2}>
              <div style={styles.pillWrap}>
                {activeTerm ? (
                  <span style={styles.pill}>
                    term filter: <b>{activeTerm}</b>{" "}
                    <button
                      style={styles.pillX}
                      onClick={() => {
                        setActiveTerm("");
                        runSearch(q, "");
                      }}
                      title="Clear term filter"
                    >
                      ×
                    </button>
                  </span>
                ) : (
                  <span style={styles.hint}>Tip: click a trending chip to search + filter.</span>
                )}
              </div>
            </div>

            {searchErr ? <div style={styles.err}>{searchErr}</div> : null}

            <div style={styles.list}>
              {results.length === 0 && !searchErr ? (
                <div style={styles.muted}>No results yet. Try searching.</div>
              ) : null}

              {results.map((p) => (
                <a
                  key={p.reddit_id}
                  href={`https://www.reddit.com/r/${p.subreddit}/comments/${p.reddit_id}/`}
                  target="_blank"
                  rel="noreferrer"
                  style={styles.item}
                >
                  <div style={styles.itemTop}>
                    <div style={styles.itemTitle}>{p.title}</div>
                  </div>
                  <div style={styles.itemMeta}>
                    <span>r/{p.subreddit}</span>
                    <span>•</span>
                    <span>{timeAgo(p.created_utc)}</span>
                    <span>•</span>
                    <span>▲ {p.score}</span>
                    <span>•</span>
                    <span>💬 {p.num_comments}</span>
                    <span>•</span>
                    <span>rank {p.rank_score}</span>
                  </div>
                </a>
              ))}
            </div>
          </section>

          {/* Right: Cuisines + Terms */}
          <aside style={styles.card}>
            {/* NEW: Trending Cuisines */}
            <div style={styles.cardTitle}>Trending Cuisines</div>

            {cuisineErr ? <div style={styles.err}>{cuisineErr}</div> : null}

            <div style={styles.chips}>
              {cuisineLoading ? (
                <div style={styles.muted}>Loading cuisines…</div>
              ) : (
                cuisines.map((c) => (
                  <button
                    key={c.origin}
                    style={styles.chip}
                    type="button"
                    title={`trend ${c.trend_score} • mentions ${c.mentions} • spread ${c.subreddit_spread} • spike ${c.spike}`}
                    onClick={() => {
                      // optional: later we can implement cuisine → term drilldown
                    }}
                  >
                    {ORIGIN_LABEL[c.origin] || c.origin}
                    <span style={styles.chipBadge}>{c.mentions}</span>
                    <span style={styles.chipBadge}>spread {c.subreddit_spread}</span>
                  </button>
                ))
              )}
            </div>

            <div style={styles.footerNote}>
              Spread = number of unique subreddits mentioning that cuisine in the selected time window.
            </div>

            <div style={styles.divider} />

            {/* Existing: Trending Terms */}
            <div style={styles.cardTitle}>Trending Terms</div>

            {trendErr ? <div style={styles.err}>{trendErr}</div> : null}

            <div style={styles.chips}>
              {trendLoading ? (
                <div style={styles.muted}>Loading trends…</div>
              ) : (
                trending.map((t) => (
                  <button key={t.term_id} onClick={() => onChip(t.term)} style={styles.chip}>
                    {t.term}
                    <span style={styles.chipBadge}>{t.mentions}</span>
                  </button>
                ))
              )}
            </div>

            <div style={styles.divider} />

            <div style={styles.cardTitleSmall}>Top 5 (quick glance)</div>
            <div style={styles.top5}>
              {top5.map((t) => (
                <div key={t.term_id} style={styles.top5Row}>
                  <div style={styles.top5Term}>{t.term}</div>
                  <div style={styles.top5Nums}>
                    <span style={styles.kv}>score {t.trend_score}</span>
                    <span style={styles.kv}>spike {t.spike}</span>
                  </div>
                </div>
              ))}
            </div>

            <div style={styles.divider} />
            <div style={styles.cardTitleSmall}>Score histogram</div>
            <div style={styles.chartWrap}>
              {trendLoading ? <div style={styles.muted}>Loading chart…</div> : <ScoresHistogram trending={trending} />}
            </div>

            <div style={styles.footerNote}>
              Click a term to instantly search + apply the term filter.
            </div>
          </aside>
        </main>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#0b0f14",
    color: "#e8eef7",
    fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial",
    padding: 24,
  },
  shell: { maxWidth: 1120, margin: "0 auto" },
  header: {
    display: "flex",
    justifyContent: "space-between",
    gap: 16,
    alignItems: "flex-start",
    marginBottom: 18,
  },
  title: { fontSize: 28, fontWeight: 800, letterSpacing: 0.2 },
  subtitle: { marginTop: 6, color: "#a8b3c7", maxWidth: 720, lineHeight: 1.35 },
  controls: { display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap" },
  label: { display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: "#a8b3c7" },
  inputSmall: {
    width: 110,
    padding: "10px 10px",
    borderRadius: 12,
    border: "1px solid #243044",
    background: "#0f1622",
    color: "#e8eef7",
    outline: "none",
  },
  grid: { display: "grid", gridTemplateColumns: "1.35fr 0.85fr", gap: 14 },
  card: {
    background: "#0f1622",
    border: "1px solid #1e2a3d",
    borderRadius: 18,
    padding: 16,
    boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
  },
  cardTitle: { fontSize: 14, fontWeight: 800, letterSpacing: 0.4, marginBottom: 10 },
  cardTitleSmall: {
    fontSize: 13,
    fontWeight: 800,
    letterSpacing: 0.3,
    marginBottom: 8,
    color: "#c9d5ea",
  },
  row: { display: "flex", gap: 10, alignItems: "center" },
  row2: { marginTop: 10, display: "flex", alignItems: "center", justifyContent: "space-between" },
  input: {
    flex: 1,
    padding: "12px 12px",
    borderRadius: 14,
    border: "1px solid #243044",
    background: "#0b111b",
    color: "#e8eef7",
    outline: "none",
  },
  btn: {
    padding: "10px 12px",
    borderRadius: 14,
    border: "1px solid #2a3a55",
    background: "#121b2a",
    color: "#e8eef7",
    cursor: "pointer",
  },
  btnPrimary: {
    padding: "12px 14px",
    borderRadius: 14,
    border: "1px solid #2a3a55",
    background: "#182338",
    color: "#e8eef7",
    cursor: "pointer",
    fontWeight: 700,
  },
  err: {
    marginTop: 10,
    padding: 10,
    borderRadius: 14,
    background: "rgba(255, 80, 80, 0.12)",
    border: "1px solid rgba(255, 80, 80, 0.25)",
    color: "#ffd7d7",
    fontSize: 13,
  },
  muted: { color: "#93a1ba", fontSize: 13 },
  list: { marginTop: 12, display: "flex", flexDirection: "column", gap: 10 },
  item: {
    textDecoration: "none",
    color: "#e8eef7",
    padding: 12,
    borderRadius: 16,
    border: "1px solid #1f2a3c",
    background: "#0b111b",
  },
  itemTop: { display: "flex", justifyContent: "space-between", gap: 8 },
  itemTitle: { fontSize: 14, fontWeight: 800, lineHeight: 1.25 },
  itemMeta: {
    marginTop: 8,
    display: "flex",
    gap: 8,
    flexWrap: "wrap",
    color: "#a8b3c7",
    fontSize: 12,
  },
  chips: { display: "flex", flexWrap: "wrap", gap: 8, marginTop: 6 },
  chip: {
    display: "inline-flex",
    gap: 8,
    alignItems: "center",
    borderRadius: 999,
    padding: "9px 11px",
    border: "1px solid #2a3a55",
    background: "#0b111b",
    color: "#e8eef7",
    cursor: "pointer",
    fontSize: 13,
  },
  chipBadge: {
    fontSize: 12,
    padding: "2px 8px",
    borderRadius: 999,
    border: "1px solid #2a3a55",
    color: "#a8b3c7",
  },
  divider: { height: 1, background: "#1e2a3d", margin: "14px 0" },
  top5: { display: "flex", flexDirection: "column", gap: 10 },
  top5Row: {
    padding: 10,
    border: "1px solid #1f2a3c",
    borderRadius: 16,
    background: "#0b111b",
  },
  top5Term: { fontWeight: 800 },
  top5Nums: { marginTop: 6, display: "flex", gap: 10, flexWrap: "wrap" },
  kv: { fontSize: 12, color: "#a8b3c7" },
  pillWrap: { display: "flex", gap: 8, alignItems: "center" },
  pill: {
    display: "inline-flex",
    gap: 8,
    alignItems: "center",
    padding: "8px 10px",
    borderRadius: 999,
    border: "1px solid #2a3a55",
    background: "#0b111b",
    fontSize: 12,
    color: "#a8b3c7",
  },
  pillX: {
    border: "none",
    background: "transparent",
    color: "#a8b3c7",
    cursor: "pointer",
    fontSize: 16,
    lineHeight: 1,
  },
  hint: { fontSize: 12, color: "#93a1ba" },
  footerNote: { marginTop: 12, fontSize: 12, color: "#93a1ba", lineHeight: 1.35 },
  chartWrap: {
    border: "1px solid #1f2a3c",
    borderRadius: 16,
    background: "#0b111b",
    padding: 10,
  },
};