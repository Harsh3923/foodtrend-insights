import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export default function ScoresHistogram({
  trending = [],
  minHeight = 320,
  rowHeight = 28,
  maxHeight = 900,
}) {
  const data = [...trending]
    .filter((t) => t?.term && t?.trend_score != null)
    .map((t) => ({
      term: t.term,
      trend_score: Number(t.trend_score),
      mentions: Number(t.mentions),
    }))
    .filter((d) => Number.isFinite(d.trend_score))
    .sort((a, b) => b.trend_score - a.trend_score);

  if (!data.length) return null;

  const computedHeight = Math.min(
    maxHeight,
    Math.max(minHeight, data.length * rowHeight)
  );

  // Custom tooltip so we can control ALL text color (black)
  function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;
    const row = payload[0].payload;

    return (
      <div
        style={{
          background: "#ffffff",
          color: "#000000",
          border: "1px solid #ccc",
          borderRadius: 10,
          padding: "10px 12px",
          boxShadow: "0 10px 24px rgba(0,0,0,0.25)",
        }}
      >
        <div style={{ fontWeight: 400, marginBottom: 6 }}>term: {label}</div>
        <div>trend score : {row.trend_score.toFixed(2)}</div>
        <div>mentions : {Number.isFinite(row.mentions) ? row.mentions : 0}</div>
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height: computedHeight }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 16, bottom: 8, left: 14 }}
        >
          <CartesianGrid stroke="#2a3a55" strokeDasharray="3 3" opacity={0.25} />

          <XAxis
            type="number"
            dataKey="trend_score"
            tick={{ fill: "#ffffff" }}
            axisLine={{ stroke: "#ffffff" }}
            tickLine={{ stroke: "#ffffff" }}
          />

          <YAxis
            type="category"
            dataKey="term"
            width={100}
            interval={0}
            tick={{ fill: "#ffffff", fontSize: 12 }}
            axisLine={{ stroke: "#ffffff" }}
            tickLine={{ stroke: "#ffffff" }}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Bars are still based on trend_score */}
          <Bar dataKey="trend_score" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}