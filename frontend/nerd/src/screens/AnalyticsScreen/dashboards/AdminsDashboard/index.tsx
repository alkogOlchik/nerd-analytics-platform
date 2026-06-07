import { useRef } from "react"
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts"
import { useSla, useAdminWorkload, useAdminSla } from "domain/Analytics"
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters"
import { FilterBar } from "../../components/FilterBar"
import { KpiCard } from "../../components/KpiCard"
import { ChartContainer } from "../../components/ChartContainer"
import { ExportToolbar } from "../../components/ExportToolbar"
import { exportCsv, exportPng, exportPdf } from "shared/utils/exportAnalytics"
import styles from "./styles.module.scss"

const COLORS = ["#4ade80", "#f87171"]
const PRIORITY_LABELS: Record<string, string> = { low: "Низкий", medium: "Средний", high: "Высокий" }

export const AdminsDashboard = () => {
  const { filters, updateFilters, resetFilters, saveConfig } = useAnalyticsFilters("admins")
  const { data: sla, isLoading: slaLoading, error: slaError } = useSla(filters)
  const { data: workload, isLoading: wlLoading } = useAdminWorkload(filters)
  const { data: adminSla, isLoading: aslLoading } = useAdminSla(filters)

  const slaPieRef = useRef<HTMLDivElement>(null)
  const workloadRef = useRef<HTMLDivElement>(null)
  const violationsRef = useRef<HTMLDivElement>(null)

  const avgTtfr =
    adminSla && adminSla.byPriority.length > 0
      ? adminSla.byPriority.reduce((s, p) => s + p.avgTtfr, 0) / adminSla.byPriority.length
      : null

  const avgTtr =
    adminSla && adminSla.byPriority.length > 0
      ? adminSla.byPriority.reduce((s, p) => s + p.avgTtr, 0) / adminSla.byPriority.length
      : null

  const pieData = [
    { key: "Соблюдено", count: sla?.compliant ?? 0 },
    { key: "Нарушено", count: sla?.breached ?? 0 },
  ]

  const workloadChartData = workload?.items.map((i) => ({
    name: i.username,
    open: i.openTickets,
    closed: i.closedTickets,
  })) ?? []

  const handleExportSvg = (ref: React.RefObject<HTMLDivElement | null>, name: string) => {
    const svg = ref.current?.querySelector("svg")
    if (svg) exportPng(svg as SVGElement, name)
  }

  return (
    <div className={styles.dashboard}>
      <FilterBar filters={filters} onChange={updateFilters} onReset={resetFilters} onSave={saveConfig} />

      <div className={styles.kpiRow}>
        <KpiCard
          label="Соблюдение SLA"
          value={slaLoading ? "—" : `${((sla?.complianceRate ?? 0) * 100).toFixed(1)}`}
          unit="%"
          highlight={
            !sla ? undefined
            : sla.complianceRate >= 0.9 ? "success"
            : sla.complianceRate >= 0.7 ? "warning"
            : "danger"
          }
        />
        <KpiCard label="Выполнено" value={slaLoading ? "—" : sla?.compliant ?? 0} highlight="success" />
        <KpiCard label="Нарушено SLA" value={slaLoading ? "—" : sla?.breached ?? 0} highlight={sla?.breached ? "danger" : undefined} />
        <KpiCard
          label="Ср. TTFR (мин)"
          value={aslLoading ? "—" : avgTtfr !== null ? avgTtfr.toFixed(0) : "—"}
        />
        <KpiCard
          label="Ср. TTR (мин)"
          value={aslLoading ? "—" : avgTtr !== null ? avgTtr.toFixed(0) : "—"}
        />
      </div>

      <div className={styles.chartsGrid}>
        <ChartContainer title="Выполнено / нарушено SLA" isLoading={slaLoading} error={slaError} containerRef={slaPieRef}>
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(pieData, "sla-compliance")}
              onExportPng={() => handleExportSvg(slaPieRef, "sla-compliance")}
              onExportPdf={() => slaPieRef.current && exportPdf(slaPieRef.current, "Соблюдение SLA")}
            />
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={pieData} dataKey="count" nameKey="key" cx="50%" cy="50%" outerRadius={100} innerRadius={50}>
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

        <ChartContainer title="Нагрузка по сотрудникам" isLoading={wlLoading} containerRef={workloadRef}>
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(workloadChartData, "admin-workload")}
              onExportPng={() => handleExportSvg(workloadRef, "admin-workload")}
              onExportPdf={() => workloadRef.current && exportPdf(workloadRef.current, "Нагрузка по сотрудникам")}
            />
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={workloadChartData} margin={{ left: 0, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: "#aaa", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                />
                <Bar dataKey="open" name="Открытые" fill="#facc15" radius={[4, 4, 0, 0]} />
                <Bar dataKey="closed" name="Закрытые" fill="#4ade80" radius={[4, 4, 0, 0]} />
                <Legend formatter={(value) => <span style={{ color: "#aaa", fontSize: 12 }}>{value}</span>} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>

        <ChartContainer title="SLA и время ответа по приоритетам" isLoading={aslLoading} containerRef={violationsRef} wide>
          {adminSla && adminSla.byPriority.length > 0 ? (
            <div className={styles.chartWithExport}>
              <ExportToolbar
                onExportCsv={() => exportCsv(adminSla.byPriority, "sla-by-priority")}
                onExportPng={() => {}}
                onExportPdf={() => {}}
              />
              <table className={styles.slaTable}>
                <thead>
                  <tr>
                    <th>Приоритет</th>
                    <th>Ср. TTFR (мин)</th>
                    <th>Ср. TTR (мин)</th>
                    <th>TTFR OK %</th>
                    <th>TTR OK %</th>
                  </tr>
                </thead>
                <tbody>
                  {adminSla.byPriority.map((row) => (
                    <tr key={row.priority}>
                      <td>{PRIORITY_LABELS[row.priority] ?? row.priority}</td>
                      <td>{row.avgTtfr.toFixed(0)}</td>
                      <td>{row.avgTtr.toFixed(0)}</td>
                      <td style={{ color: row.slaTtfrCompliancePct >= 90 ? "#4ade80" : row.slaTtfrCompliancePct >= 70 ? "#facc15" : "#f87171" }}>
                        {row.slaTtfrCompliancePct.toFixed(1)}%
                      </td>
                      <td style={{ color: row.slaTtrCompliancePct >= 90 ? "#4ade80" : row.slaTtrCompliancePct >= 70 ? "#facc15" : "#f87171" }}>
                        {row.slaTtrCompliancePct.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {adminSla.topViolatedCategories.length > 0 && (
                <div className={styles.violationsList}>
                  <h4 className={styles.violationsTitle}>Топ нарушений по категориям</h4>
                  <div className={styles.tagList}>
                    {adminSla.topViolatedCategories.map((c) => (
                      <span key={c.category} className={styles.tag}>
                        {c.category} <span className={styles.tagCount}>{c.count}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className={styles.empty}>Нет данных за период</div>
          )}
        </ChartContainer>
      </div>
    </div>
  )
}
