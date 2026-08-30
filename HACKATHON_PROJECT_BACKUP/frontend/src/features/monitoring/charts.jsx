import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const tooltipStyle = {
  backgroundColor: "#121a2f",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  color: "#e2e8f0",
};

export function CpuChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <defs>
          <linearGradient id="cpuFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.35} />
            <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.06)" />
        <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} />
        <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
        <Tooltip contentStyle={tooltipStyle} />
        <Area type="monotone" dataKey="value" name="CPU %" stroke="#22d3ee" fill="url(#cpuFill)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function RamChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <CartesianGrid stroke="rgba(255,255,255,0.06)" />
        <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} />
        <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} unit="%" />
        <Tooltip contentStyle={tooltipStyle} />
        <Line type="monotone" dataKey="value" name="RAM %" stroke="#a78bfa" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function SecurityEventsChart({ timeline, byType }) {
  return (
    <div className="grid h-full grid-rows-2 gap-3">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={timeline}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
          <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="count" name="Events" fill="#f08a3e" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={byType} layout="vertical">
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis type="number" stroke="#94a3b8" fontSize={11} allowDecimals={false} />
          <YAxis type="category" dataKey="event_type" stroke="#94a3b8" fontSize={10} width={110} />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="count" name="Count" fill="#22d3ee" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function AlertTrendsChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data}>
        <CartesianGrid stroke="rgba(255,255,255,0.06)" />
        <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} />
        <YAxis stroke="#94a3b8" fontSize={11} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Legend />
        <Area type="monotone" dataKey="critical" stackId="1" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.7} />
        <Area type="monotone" dataKey="high" stackId="1" stroke="#f08a3e" fill="#f08a3e" fillOpacity={0.7} />
        <Area type="monotone" dataKey="medium" stackId="1" stroke="#eab308" fill="#eab308" fillOpacity={0.55} />
        <Area type="monotone" dataKey="low" stackId="1" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.4} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
