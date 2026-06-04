import { useRef } from "react"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts"
import { useReviewsSummary, useReviewsKeywords } from "domain/Analytics"
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters"
import { FilterBar } from "../../components/FilterBar"
import { KpiCard } from "../../components/KpiCard"
import { ChartContainer } from "../../components/ChartContainer"
import { ExportToolbar } from "../../components/ExportToolbar"
import { exportCsv, exportPng, exportPdf } from "shared/utils/exportAnalytics"
import styles from "./styles.module.scss"

export const ReviewsDashboard = () => {
  const { filters, updateFilters, resetFilters, saveConfig } = useAnalyticsFilters("reviews")
  const { data: summary, isLoading: summaryLoading, error: summaryError } = useReviewsSummary(filters)
  const { data: keywords, isLoading: keywordsLoading } = useReviewsKeywords(filters)

  const sentimentRef = useRef<HTMLDivElement>(null)

  return (
    <div className={styles.dashboard}>
      <FilterBar filters={filters} onChange={updateFilters} onReset={resetFilters} onSave={saveConfig} />

      <div className={styles.kpiRow}>
        <KpiCard
          label="Средний рейтинг (CSAT)"
          value={summaryLoading ? "—" : (summary?.averageRating ?? 0).toFixed(1)}
          unit="/ 5"
          highlight={
            !summary ? undefined
            : summary.averageRating >= 4 ? "success"
            : summary.averageRating >= 3 ? "warning"
            : "danger"
          }
        />
        <KpiCard
          label="Всего отзывов"
          value={summaryLoading ? "—" : (summary?.totalReviews ?? 0).toLocaleString()}
        />
      </div>

      <ChartContainer
        title="Распределение тональности"
        isLoading={summaryLoading}
        error={summaryError}
        containerRef={sentimentRef}
      >
        <div className={styles.chartWithExport}>
          <ExportToolbar
            onExportCsv={() => exportCsv(summary?.sentimentDistribution ?? [], "reviews-sentiment")}
            onExportPng={() => { const svg = sentimentRef.current?.querySelector("svg"); if (svg) exportPng(svg as SVGElement, "reviews-sentiment") }}
            onExportPdf={() => sentimentRef.current && exportPdf(sentimentRef.current, "Тональность отзывов")}
          />
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={summary?.sentimentDistribution} margin={{ left: 0, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="key" tick={{ fill: "#aaa", fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                labelStyle={{ color: "#fff" }}
                itemStyle={{ color: "#c4b5fd" }}
              />
              <Bar dataKey="count" name="Отзывы" fill="#7c5cff" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </ChartContainer>

      <div className={styles.keywordsGrid}>
        <div className={styles.keywordsCard}>
          <div className={styles.keywordsHeader}>
            <h4 className={styles.keywordsTitle}>Позитивные ключевые слова</h4>
            {!keywordsLoading && (
              <ExportToolbar
                onExportCsv={() => exportCsv(keywords?.keywordsPositive ?? [], "keywords-positive")}
                onExportPng={() => {}}
                onExportPdf={() => {}}
              />
            )}
          </div>
          <KeywordsTable data={keywords?.keywordsPositive ?? []} isLoading={keywordsLoading} accentColor="#4ade80" />
        </div>

        <div className={styles.keywordsCard}>
          <div className={styles.keywordsHeader}>
            <h4 className={styles.keywordsTitle}>Негативные ключевые слова</h4>
            {!keywordsLoading && (
              <ExportToolbar
                onExportCsv={() => exportCsv(keywords?.keywordsNegative ?? [], "keywords-negative")}
                onExportPng={() => {}}
                onExportPdf={() => {}}
              />
            )}
          </div>
          <KeywordsTable data={keywords?.keywordsNegative ?? []} isLoading={keywordsLoading} accentColor="#f87171" />
        </div>
      </div>
    </div>
  )
}

const KeywordsTable = ({
  data,
  isLoading,
  accentColor,
}: {
  data: { key: string; count: number }[]
  isLoading: boolean
  accentColor: string
}) => {
  if (isLoading) return <div className={styles.tableLoading}>Загрузка…</div>
  if (!data.length) return <div className={styles.tableEmpty}>Нет данных</div>
  return (
    <table className={styles.table}>
      <thead>
        <tr>
          <th>Слово</th>
          <th>Упоминаний</th>
        </tr>
      </thead>
      <tbody>
        {data.map((row) => (
          <tr key={row.key}>
            <td style={{ color: accentColor }}>{row.key}</td>
            <td>{row.count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
