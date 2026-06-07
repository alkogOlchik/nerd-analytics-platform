import { useRef } from "react"
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts"
import { useAiAccuracy, useAiEfficiency } from "domain/Analytics"
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters"
import { FilterBar } from "../../components/FilterBar"
import { KpiCard } from "../../components/KpiCard"
import { ChartContainer } from "../../components/ChartContainer"
import { ExportToolbar } from "../../components/ExportToolbar"
import { exportCsv, exportPng, exportPdf } from "shared/utils/exportAnalytics"
import styles from "./styles.module.scss"

const COLORS_PIE = ["#7c5cff", "#f87171"]
const COLOR_ESCALATED = "#f87171"
const COLOR_RESOLVED = "#4ade80"

export const AiDashboard = () => {
  const { filters, updateFilters, resetFilters, saveConfig } = useAnalyticsFilters("ai")
  const { data: accuracy, isLoading: accLoading, error: accError } = useAiAccuracy(filters)
  const { data: efficiency, isLoading: effLoading, error: effError } = useAiEfficiency(filters)

  const classificationRef = useRef<HTMLDivElement>(null)
  const escalatedRef = useRef<HTMLDivElement>(null)
  const resolvedRef = useRef<HTMLDivElement>(null)

  const autoCount = (accuracy?.totalClassified ?? 0) - (accuracy?.adminChanged ?? 0)
  const pieData = [
    { key: "Автоматически", count: autoCount },
    { key: "Изменено вручную", count: accuracy?.adminChanged ?? 0 },
  ]

  const handleExportSvg = (ref: React.RefObject<HTMLDivElement | null>, name: string) => {
    const svg = ref.current?.querySelector("svg")
    if (svg) exportPng(svg as SVGElement, name)
  }

  return (
    <div className={styles.dashboard}>
      <FilterBar filters={filters} onChange={updateFilters} onReset={resetFilters} onSave={saveConfig} />

      <div className={styles.kpiRow}>
        <KpiCard
          label="Точность классификации"
          value={accLoading ? "—" : `${((accuracy?.accuracyRate ?? 0) * 100).toFixed(1)}`}
          unit="%"
          highlight={
            !accuracy ? undefined
            : accuracy.accuracyRate >= 0.9 ? "success"
            : accuracy.accuracyRate >= 0.7 ? "warning"
            : "danger"
          }
        />
        <KpiCard
          label="Изменено администратором"
          value={accLoading ? "—" : accuracy?.adminChanged ?? 0}
        />
        <KpiCard
          label="Всего классифицировано"
          value={accLoading ? "—" : accuracy?.totalClassified ?? 0}
        />
        <KpiCard
          label="Авторазрешено ИИ"
          value={effLoading ? "—" : `${(efficiency?.autoResolvedPct ?? 0).toFixed(1)}`}
          unit="%"
          highlight={
            !efficiency ? undefined
            : efficiency.autoResolvedPct >= 50 ? "success"
            : efficiency.autoResolvedPct >= 25 ? "warning"
            : "danger"
          }
        />
        <KpiCard
          label="Эскалировано"
          value={effLoading ? "—" : efficiency?.escalated ?? 0}
          highlight={efficiency?.escalated ? "warning" : undefined}
        />
        <KpiCard
          label="Сообщений до эскалации"
          value={effLoading ? "—" : (efficiency?.avgMessagesBeforeEscalation ?? 0).toFixed(1)}
        />
      </div>

      <div className={styles.chartsGrid}>
        <ChartContainer
          title="Соотношение авто / ручная классификация"
          isLoading={accLoading}
          error={accError}
          containerRef={classificationRef}
        >
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(pieData, "ai-classification")}
              onExportPng={() => handleExportSvg(classificationRef, "ai-classification")}
              onExportPdf={() => classificationRef.current && exportPdf(classificationRef.current, "Классификация ИИ")}
            />
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={pieData} dataKey="count" nameKey="key" cx="50%" cy="50%" outerRadius={100} innerRadius={50}>
                  {pieData.map((entry, i) => (
                    <Cell key={entry.key} fill={COLORS_PIE[i % COLORS_PIE.length]} />
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

        <ChartContainer
          title="Топ категорий эскалации"
          isLoading={effLoading}
          error={effError}
          containerRef={escalatedRef}
        >
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(efficiency?.topEscalatedCategories ?? [], "ai-escalated")}
              onExportPng={() => handleExportSvg(escalatedRef, "ai-escalated")}
              onExportPdf={() => escalatedRef.current && exportPdf(escalatedRef.current, "Категории эскалации")}
            />
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={efficiency?.topEscalatedCategories ?? []} layout="vertical" margin={{ left: 16, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="category" type="category" width={130} tick={{ fill: "#aaa", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                  itemStyle={{ color: COLOR_ESCALATED }}
                />
                <Bar dataKey="count" name="Эскалации" fill={COLOR_ESCALATED} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>

        <ChartContainer
          title="Топ категорий авторазрешения"
          isLoading={effLoading}
          error={effError}
          containerRef={resolvedRef}
        >
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(efficiency?.topResolvedCategories ?? [], "ai-resolved")}
              onExportPng={() => handleExportSvg(resolvedRef, "ai-resolved")}
              onExportPdf={() => resolvedRef.current && exportPdf(resolvedRef.current, "Категории авторазрешения")}
            />
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={efficiency?.topResolvedCategories ?? []} layout="vertical" margin={{ left: 16, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="category" type="category" width={130} tick={{ fill: "#aaa", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                  itemStyle={{ color: COLOR_RESOLVED }}
                />
                <Bar dataKey="count" name="Авторазрешено" fill={COLOR_RESOLVED} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>
      </div>
    </div>
  )
}
