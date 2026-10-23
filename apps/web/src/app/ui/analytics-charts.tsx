"use client";

import { useState } from "react";
import type { Overview } from "@/lib/analytics-types";

export const riskColors: Record<string, string> = {
  CRITICAL: "#f04452", HIGH: "#ff854a", MEDIUM: "#f4b544", LOW: "#16c79a",
};

export function RiskDonut({ distribution, threshold }: {
  distribution: Overview["distribution"]; threshold: number;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const total = distribution.reduce((sum, item) => sum + item.count, 0);
  let offset = 0;
  const segments = ["CRITICAL", "HIGH", "MEDIUM", "LOW"].map(severity => {
    const count = distribution.find(item => item.severity === severity)?.count ?? 0;
    const length = total ? count / total * 100 : 0;
    const item = { severity, count, length, offset };
    offset += length;
    return item;
  });
  return <div className="risk-distribution">
    <div className="donut-visual">
      <svg viewBox="0 0 140 140" role="img" aria-label={`Risk distribution for ${total} cases`}>
        <circle cx="70" cy="70" r="52" fill="none" stroke="#153047" strokeWidth="13"/>
        {segments.map(item => <circle key={item.severity} cx="70" cy="70" r="52" fill="none"
          stroke={riskColors[item.severity]} strokeWidth={selected === item.severity ? 17 : 13}
          pathLength="100" strokeDasharray={`${Math.max(0, item.length - 1)} ${101 - item.length}`}
          strokeDashoffset={-item.offset} transform="rotate(-90 70 70)"
          opacity={selected && selected !== item.severity ? .3 : 1}>
          <title>{`${item.severity}: ${item.count} cases`}</title>
        </circle>)}
      </svg><div className="donut-label"><strong>{selected ? segments.find(x => x.severity === selected)?.count : total}</strong><span>{selected?.toLowerCase() ?? "total cases"}</span></div>
    </div>
    <div className="risk-legend">{segments.map(item => <button key={item.severity} aria-pressed={selected === item.severity} onClick={() => setSelected(selected === item.severity ? null : item.severity)}>
      <i style={{ background: riskColors[item.severity] }}/><span>{item.severity.toLowerCase()}</span><strong>{item.count}</strong><small>{total ? Math.round(item.count / total * 100) : 0}%</small>
    </button>)}<p>Critical threshold: {threshold}/100</p></div>
  </div>;
}

const series = [
  { key: "created", label: "Cases created", color: "#12b8d0" },
  { key: "completed", label: "Runs completed", color: "#00d6b2" },
  { key: "high_risk", label: "High-risk runs", color: "#ff854a" },
  { key: "evidence", label: "Files processed", color: "#9d8cf2" },
] as const;

export function TrendChart({ data }: { data: Overview["trend"] }) {
  const [hidden, setHidden] = useState<string[]>([]);
  const visible = series.filter(item => !hidden.includes(item.key));
  const max = Math.max(1, ...data.flatMap(row => visible.map(item => row[item.key])));
  const width = 580, height = 164, left = 28, top = 12;
  return <div className="trend-chart">
    <svg viewBox="0 0 620 205" role="img" aria-label="Daily case creation, completed runs, high-risk runs and evidence processing">
      {[0, .5, 1].map(t => <g key={t}><line x1={left} x2={width + left} y1={top + height * t} y2={top + height * t} stroke="#183044" strokeDasharray="3 4"/><text x="2" y={top + height * t + 4} fill="#72899c" fontSize="10">{Math.round(max * (1 - t))}</text></g>)}
      {visible.map(item => <polyline key={item.key} points={data.map((row, index) =>
        `${left + index * width / Math.max(1, data.length - 1)},${top + height - row[item.key] / max * height}`).join(" ")}
        stroke={item.color} strokeWidth="2" fill="none" strokeLinejoin="round"/>)}
      {data.map((row, index) => index % Math.max(1, Math.floor(data.length / 6)) === 0 && <text key={row.date} x={left + index * width / Math.max(1, data.length - 1)} y="198" textAnchor="middle" fill="#72899c" fontSize="10">{row.date.slice(5)}</text>)}
    </svg>
    <div className="chart-legend">{series.map(item => <button aria-pressed={!hidden.includes(item.key)} key={item.key} onClick={() => setHidden(current => current.includes(item.key) ? current.filter(x => x !== item.key) : [...current, item.key])}><i style={{ background: item.color }}/>{item.label}</button>)}</div>
    <details className="chart-data"><summary>View chart data</summary><table><caption>Daily activity</caption><thead><tr><th>Date</th>{series.map(item => <th key={item.key}>{item.label}</th>)}</tr></thead><tbody>{data.map(row => <tr key={row.date}><td>{row.date}</td>{series.map(item => <td key={item.key}>{row[item.key]}</td>)}</tr>)}</tbody></table></details>
  </div>;
}
