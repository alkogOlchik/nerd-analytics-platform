import { useRef } from "react"
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from "recharts"
import { useAiAccuracy } from "domain/Analytics"
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters"
import { FilterBar } from "../../components/FilterBar"
import { KpiCard } from "../../components/KpiCard"
import { ChartContainer } from "../../components/ChartContainer"
import { ExportToolbar } from "../../components/ExportToolbar"
import { exportCsv, exportPng, exportPdf } from "shared/utils/exportAnalytics"
import styles from "./styles.module.scss"

const COLORS = ["#7c5cff", "#f87171"]

export const AiDashboard = () => {
  const { filters, updateFilters, resetFilters, saveConfig } = useAnalyticsFilters("ai")
  const { data, isLoading, error } = useAiAccuracy(filters)
  const chartRef = useRef<HTMLDivElement>(null)

  const autoCount = (data?.totalClassified ?? 0) - (data?.adminChanged ?? 0)
  const pieData = [
    { key: "Автоматически", count: autoCount },
    { key: "Изменено вручную", count: data?.adminChanged ?? 0 },
  ]

  return (
    <div className={styles.dashboard}>
      <FilterBar filters={filters} onChange={updateFilters} onReset={resetFilters} onSave={saveConfig} />

      <div className={styles.kpiRow}>
        <KpiCard
          label="Точность классификации"
          value={isLoading ? "—" : `${((data?.accuracyRate ?? 0) * 100).toFixed(1)}`}
          unit="%"
          highlight={
            !data ? undefined
            : data.accuracyRate >= 0.9 ? "success"
            : data.accuracyRate >= 0.7 ? "warning"
            : "danger"
          }
        />
        <KpiCard
          label="Изменено администратором"
          value={isLoading ? "—" : data?.adminChanged ?? 0}
        />
        <KpiCard
          label="Всего классифицировано"
          value={isLoading ? "—" : data?.totalClassified ?? 0}
        />
      </div>

      <ChartContainer
        title="Соотношение авто / ручная классификация"
        isLoading={isLoading}
        error={error}
        containerRef={chartRef}
      >
        <div className={styles.chartWithExport}>
          <ExportToolbar
            onExportCsv={() => exportCsv(pieData, "ai-classification")}
            onExportPng={() => { const svg = chartRef.current?.querySelector("svg"); if (svg) exportPng(svg as SVGElement, "ai-classification") }}
            onExportPdf={() => chartRef.current && exportPdf(chartRef.current, "Классификация ИИ")}
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
