import { useRef, useState } from "react"
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts"
import { useTicketSummary } from "domain/Analytics"
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters"
import { FilterBar } from "../../components/FilterBar"
import { KpiCard } from "../../components/KpiCard"
import { ChartContainer } from "../../components/ChartContainer"
import { ExportToolbar } from "../../components/ExportToolbar"
import { exportCsv, exportPng, exportPdf } from "shared/utils/exportAnalytics"
import styles from "./styles.module.scss"

const COLORS = ["#7c5cff", "#4ade80", "#facc15", "#f87171", "#60a5fa", "#f472b6"]

export const OverviewDashboard = () => {
  const { filters, updateFilters, resetFilters, saveConfig } = useAnalyticsFilters("overview")
  const { data, isLoading, error } = useTicketSummary(filters)

  const statusRef = useRef<HTMLDivElement>(null)
  const productRef = useRef<HTMLDivElement>(null)
  const categoryRef = useRef<HTMLDivElement>(null)

  const [hiddenStatus, setHiddenStatus] = useState<Set<string>>(new Set())

  const openCount = data?.byStatus.find((s) => s.key === "open")?.count ?? 0

  const toggleStatus = (key: string) =>
    setHiddenStatus((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const handleExportSvg = (ref: React.RefObject<HTMLDivElement | null>, name: string) => {
    const svg = ref.current?.querySelector("svg")
    if (svg) exportPng(svg as SVGElement, name)
  }

  return (
    <div className={styles.dashboard}>
      <FilterBar filters={filters} onChange={updateFilters} onReset={resetFilters} onSave={saveConfig} />

      <div className={styles.kpiRow}>
        <KpiCard label="Открытые тикеты" value={isLoading ? "—" : openCount} highlight={openCount > 0 ? "warning" : "success"} />
        <KpiCard label="Всего статусов" value={isLoading ? "—" : data?.byStatus.length ?? 0} />
        <KpiCard label="Продуктов" value={isLoading ? "—" : data?.byProduct.length ?? 0} />
        <KpiCard label="Категорий" value={isLoading ? "—" : data?.byCategory.length ?? 0} />
      </div>

      <div className={styles.chartsGrid}>
        <ChartContainer title="Распределение по статусам" isLoading={isLoading} error={error} containerRef={statusRef}>
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(data?.byStatus ?? [], "tickets-by-status")}
              onExportPng={() => handleExportSvg(statusRef, "tickets-by-status")}
              onExportPdf={() => statusRef.current && exportPdf(statusRef.current, "Статусы тикетов")}
            />
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={data?.byStatus}
                  dataKey="count"
                  nameKey="key"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  onClick={(entry) => toggleStatus(entry.key)}
                >
                  {data?.byStatus.map((entry, i) => (
                    <Cell
                      key={entry.key}
                      fill={COLORS[i % COLORS.length]}
                      opacity={hiddenStatus.has(entry.key) ? 0.2 : 1}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                  itemStyle={{ color: "#c4b5fd" }}
                />
                <Legend
                  formatter={(value) => <span style={{ color: "#aaa", fontSize: 12 }}>{value}</span>}
                  onClick={(e) => toggleStatus(e.value)}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>

        <ChartContainer title="Распределение по продуктам" isLoading={isLoading} error={error} containerRef={productRef}>
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(data?.byProduct ?? [], "tickets-by-product")}
              onExportPng={() => handleExportSvg(productRef, "tickets-by-product")}
              onExportPdf={() => productRef.current && exportPdf(productRef.current, "Тикеты по продуктам")}
            />
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data?.byProduct} layout="vertical" margin={{ left: 16, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="key" type="category" width={120} tick={{ fill: "#aaa", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                  itemStyle={{ color: "#c4b5fd" }}
                />
                <Bar dataKey="count" name="Тикеты" fill="#7c5cff" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>

        <ChartContainer title="Распределение по категориям" isLoading={isLoading} error={error} containerRef={categoryRef}>
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(data?.byCategory ?? [], "tickets-by-category")}
              onExportPng={() => handleExportSvg(categoryRef, "tickets-by-category")}
              onExportPdf={() => categoryRef.current && exportPdf(categoryRef.current, "Тикеты по категориям")}
            />
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data?.byCategory} layout="vertical" margin={{ left: 16, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="key" type="category" width={120} tick={{ fill: "#aaa", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                  itemStyle={{ color: "#c4b5fd" }}
                />
                <Bar dataKey="count" name="Тикеты" fill="#60a5fa" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>
      </div>
    </div>
  )
}
