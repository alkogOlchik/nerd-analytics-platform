import { useRef } from "react"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts"
import { useUsersDemographics, useUsersRetention } from "domain/Analytics"
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters"
import { FilterBar } from "../../components/FilterBar"
import { KpiCard } from "../../components/KpiCard"
import { ChartContainer } from "../../components/ChartContainer"
import { ExportToolbar } from "../../components/ExportToolbar"
import { exportCsv, exportPng, exportPdf } from "shared/utils/exportAnalytics"
import styles from "./styles.module.scss"

export const UsersDashboard = () => {
  const { filters, updateFilters, resetFilters, saveConfig } = useAnalyticsFilters("users")
  const { data: demographics, isLoading: demoLoading, error: demoError } = useUsersDemographics(filters)
  const { data: retention, isLoading: retLoading } = useUsersRetention(filters)

  const genderRef = useRef<HTMLDivElement>(null)
  const ageRef = useRef<HTMLDivElement>(null)
  const cityRef = useRef<HTMLDivElement>(null)

  const totalUsers = demographics
    ? demographics.byGender.reduce((s, g) => s + g.count, 0)
    : null

  const handleExportSvg = (ref: React.RefObject<HTMLDivElement | null>, name: string) => {
    const svg = ref.current?.querySelector("svg")
    if (svg) exportPng(svg as SVGElement, name)
  }

  return (
    <div className={styles.dashboard}>
      <FilterBar filters={filters} onChange={updateFilters} onReset={resetFilters} onSave={saveConfig} hidePriority />

      <div className={styles.kpiRow}>
        <KpiCard label="Всего пользователей" value={demoLoading ? "—" : totalUsers ?? 0} />
        <KpiCard
          label="Удержание 7 дней"
          value={retLoading ? "—" : `${(retention?.retention7dPct ?? 0).toFixed(1)}`}
          unit="%"
          highlight={
            !retention ? undefined
            : retention.retention7dPct >= 60 ? "success"
            : retention.retention7dPct >= 30 ? "warning"
            : "danger"
          }
        />
        <KpiCard
          label="Удержание 14 дней"
          value={retLoading ? "—" : `${(retention?.retention14dPct ?? 0).toFixed(1)}`}
          unit="%"
          highlight={
            !retention ? undefined
            : retention.retention14dPct >= 40 ? "success"
            : retention.retention14dPct >= 20 ? "warning"
            : "danger"
          }
        />
        <KpiCard
          label="Удержание 30 дней"
          value={retLoading ? "—" : `${(retention?.retention30dPct ?? 0).toFixed(1)}`}
          unit="%"
          highlight={
            !retention ? undefined
            : retention.retention30dPct >= 20 ? "success"
            : retention.retention30dPct >= 10 ? "warning"
            : "danger"
          }
        />
      </div>

      <div className={styles.chartsGrid}>
        <ChartContainer title="По полу" isLoading={demoLoading} error={demoError} containerRef={genderRef}>
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(demographics?.byGender ?? [], "users-by-gender")}
              onExportPng={() => handleExportSvg(genderRef, "users-by-gender")}
              onExportPdf={() => genderRef.current && exportPdf(genderRef.current, "Пользователи по полу")}
            />
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={demographics?.byGender ?? []} margin={{ left: 0, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="key" tick={{ fill: "#aaa", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                  itemStyle={{ color: "#c4b5fd" }}
                />
                <Bar dataKey="count" name="Пользователи" fill="#7c5cff" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>

        <ChartContainer title="По возрастным группам" isLoading={demoLoading} error={demoError} containerRef={ageRef}>
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(demographics?.byAgeGroup ?? [], "users-by-age")}
              onExportPng={() => handleExportSvg(ageRef, "users-by-age")}
              onExportPdf={() => ageRef.current && exportPdf(ageRef.current, "Пользователи по возрасту")}
            />
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={demographics?.byAgeGroup ?? []} margin={{ left: 0, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="key" tick={{ fill: "#aaa", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                  itemStyle={{ color: "#c4b5fd" }}
                />
                <Bar dataKey="count" name="Пользователи" fill="#60a5fa" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>

        <ChartContainer title="По городам (топ-10)" isLoading={demoLoading} error={demoError} containerRef={cityRef} wide>
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(demographics?.byCity ?? [], "users-by-city")}
              onExportPng={() => handleExportSvg(cityRef, "users-by-city")}
              onExportPdf={() => cityRef.current && exportPdf(cityRef.current, "Пользователи по городам")}
            />
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={(demographics?.byCity ?? []).slice(0, 10)} layout="vertical" margin={{ left: 16, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="key" type="category" width={100} tick={{ fill: "#aaa", fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                  itemStyle={{ color: "#c4b5fd" }}
                />
                <Bar dataKey="count" name="Пользователи" fill="#f472b6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>
      </div>
    </div>
  )
}
