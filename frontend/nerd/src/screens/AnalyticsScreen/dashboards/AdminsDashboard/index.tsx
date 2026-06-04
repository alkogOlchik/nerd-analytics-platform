import { useRef } from "react"
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from "recharts"
import { useSla } from "domain/Analytics"
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters"
import { FilterBar } from "../../components/FilterBar"
import { KpiCard } from "../../components/KpiCard"
import { ChartContainer } from "../../components/ChartContainer"
import { ExportToolbar } from "../../components/ExportToolbar"
import { exportCsv, exportPng, exportPdf } from "shared/utils/exportAnalytics"
import styles from "./styles.module.scss"

const COLORS = ["#4ade80", "#f87171"]

export const AdminsDashboard = () => {
  const { filters, updateFilters, resetFilters, saveConfig } = useAnalyticsFilters("admins")
  const { data, isLoading, error } = useSla(filters)
  const chartRef = useRef<HTMLDivElement>(null)

  const pieData = [
    { key: "Соблюдено", count: data?.compliant ?? 0 },
    { key: "Нарушено", count: data?.breached ?? 0 },
  ]

  return (
    <div className={styles.dashboard}>
      <FilterBar filters={filters} onChange={updateFilters} onReset={resetFilters} onSave={saveConfig} />

      <div className={styles.kpiRow}>
        <KpiCard
          label="Соблюдение SLA"
          value={isLoading ? "—" : `${((data?.complianceRate ?? 0) * 100).toFixed(1)}`}
          unit="%"
          highlight={
            !data ? undefined
            : data.complianceRate >= 0.9 ? "success"
            : data.complianceRate >= 0.7 ? "warning"
            : "danger"
          }
        />
        <KpiCard label="Выполнено" value={isLoading ? "—" : data?.compliant ?? 0} highlight="success" />
        <KpiCard label="Нарушено SLA" value={isLoading ? "—" : data?.breached ?? 0} highlight={data?.breached ? "danger" : undefined} />
        <KpiCard label="TTR (среднее)" value="—" placeholder />
        <KpiCard label="TTFR (среднее)" value="—" placeholder />
      </div>

      <ChartContainer
        title="Выполнено / нарушено SLA"
        isLoading={isLoading}
        error={error}
        containerRef={chartRef}
      >
        <div className={styles.chartWithExport}>
          <ExportToolbar
            onExportCsv={() => exportCsv(pieData, "sla-compliance")}
            onExportPng={() => { const svg = chartRef.current?.querySelector("svg"); if (svg) exportPng(svg as SVGElement, "sla-compliance") }}
            onExportPdf={() => chartRef.current && exportPdf(chartRef.current, "Соблюдение SLA")}
          />
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="count"
                nameKey="key"
                cx="50%"
                cy="50%"
                outerRadius={100}
                innerRadius={50}
              >
                {pieData.map((entry, i) => (
                  <Cell key={entry.key} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                labelStyle={{ color: "#fff" }}
                itemStyle={{ color: "#c4b5fd" }}
              />
              <Legend formatter={(value) => <span style={{ color: "#aaa", fontSize: 12 }}>{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </ChartContainer>
    </div>
  )
}
