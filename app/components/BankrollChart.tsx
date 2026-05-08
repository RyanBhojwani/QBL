"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { DailyCurvePoint } from "@/lib/performance";

export default function BankrollChart({ data }: { data: DailyCurvePoint[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[240px] rounded-[12px] border border-qbl-border bg-bg-surface text-text-muted text-sm">
        No chart data available for this period.
      </div>
    );
  }

  const formatted = data.map((d) => ({
    ...d,
    label: d.date.slice(5).replace("-", "/"),
  }));

  // Start Y axis well above zero so the curve detail is visible
  const minVal = data.reduce(
    (m, d) => Math.min(m, d.bankroll_real, d.bankroll_exp),
    Infinity
  );
  const yMin = Math.max(400, Math.floor((minVal * 0.9) / 100) * 100);

  const tickInterval = Math.max(1, Math.floor(data.length / 6));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={formatted} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="rgba(255,255,255,0.07)"
          vertical={false}
        />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          tickLine={{ stroke: "#374151" }}
          axisLine={{ stroke: "#374151" }}
          interval={tickInterval}
        />
        <YAxis
          tickFormatter={(v: number) => `$${v.toFixed(0)}`}
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          tickLine={{ stroke: "#374151" }}
          axisLine={{ stroke: "#374151" }}
          width={72}
          domain={[yMin, "auto"]}
        />
        <Tooltip
          contentStyle={{
            background: "#0a0e17",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 8,
            fontSize: 12,
            color: "#e2e8f0",
          }}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={(value: any, name: any) => [
            typeof value === "number" ? `$${value.toFixed(2)}` : String(value),
            name === "bankroll_real" ? "Real" : "Expected (CLV)",
          ]}
          labelStyle={{ color: "#9ca3af", marginBottom: 4 }}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, color: "#9ca3af", paddingTop: 8 }}
          formatter={(value: string) =>
            value === "bankroll_real" ? "Real Bankroll" : "Expected (CLV)"
          }
        />
        {/* $1,000 break-even reference line */}
        <ReferenceLine
          y={1000}
          stroke="rgba(255,255,255,0.55)"
          strokeWidth={1.5}
          label={{
            value: "$1,000",
            position: "insideTopRight",
            fill: "rgba(255,255,255,0.45)",
            fontSize: 10,
          }}
        />
        <Line
          type="monotone"
          dataKey="bankroll_real"
          stroke="#00d4aa"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "#00d4aa" }}
        />
        <Line
          type="monotone"
          dataKey="bankroll_exp"
          stroke="#6b7280"
          strokeWidth={2}
          dot={false}
          strokeDasharray="5 5"
          activeDot={{ r: 4, fill: "#6b7280" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
