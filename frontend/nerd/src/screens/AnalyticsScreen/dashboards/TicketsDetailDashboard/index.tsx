import { useRef } from "react"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts"
import { useDashboard6Tickets, useTicketForecast } from "domain/Analytics"
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters"
import { FilterBar } from "../../components/FilterBar"
import { ChartContainer } from "../../components/ChartContainer"
import { ExportToolbar } from "../../components/ExportToolbar"
import { exportCsv, exportPng, exportPdf } from "shared/utils/exportAnalytics"
import styles from "./styles.module.scss"

export const TicketsDetailDashboard = () => {
  const analysis = useAnalyticsFilters("tickets-analysis")
  const forecast = useAnalyticsFilters("tickets-forecast")

  const { data: d6, isLoading: d6Loading, error: d6Error } = useDashboard6Tickets(analysis.filters)
  const { data: forecastData, isLoading: fcLoading, error: fcError } = useTicketForecast({
    product: forecast.filters.product,
    category: forecast.filters.category,
  })

  const keywordsRef = useRef<HTMLDivElement>(null)
  const forecastRef = useRef<HTMLDivElement>(null)

  const handleExportSvg = (ref: React.RefObject<HTMLDivElement | null>, name: string) => {
    const svg = ref.current?.querySelector("svg")
    if (svg) exportPng(svg as SVGElement, name)
  }

  return (
    <div className={styles.dashboard}>
      {/* Анализ тикетов */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>Анализ тикетов</h3>
        <FilterBar
          filters={analysis.filters}
          onChange={analysis.updateFilters}
          onReset={analysis.resetFilters}
          onSave={analysis.saveConfig}
        />

        <div className={styles.keywordsGrid}>
          <div className={styles.keywordsCard}>
            <div className={styles.keywordsHeader}>
              <h4 className={styles.keywordsCardTitle}>Ключевые слова тикетов</h4>
              <ExportToolbar
                onExportCsv={() => exportCsv(d6?.topKeywords ?? [], "tickets-keywords")}
                onExportPng={() => {}}
                onExportPdf={() => {}}
              />
            </div>
            <KeywordsTable
              data={(d6?.topKeywords ?? []).map((w) => ({ key: w.word, count: w.count }))}
              isLoading={d6Loading}
              accentColor="#c4b5fd"
            />
          </div>

          <div className={styles.keywordsCard}>
            <div className={styles.keywordsHeader}>
              <h4 className={styles.keywordsCardTitle}>Топ категорий</h4>
              <ExportToolbar
                onExportCsv={() => exportCsv(d6?.topCategories ?? [], "tickets-categories")}
                onExportPng={() => {}}
                onExportPdf={() => {}}
              />
            </div>
            <KeywordsTable
              data={(d6?.topCategories ?? []).map((c) => ({ key: c.category, count: c.count }))}
              isLoading={d6Loading}
              accentColor="#60a5fa"
            />
          </div>
        </div>

        <div className={styles.keywordsGrid}>
          <div className={styles.keywordsCard}>
            <div className={styles.keywordsHeader}>
              <h4 className={styles.keywordsCardTitle}>Медленные категории (ср. TTR)</h4>
              <ExportToolbar
                onExportCsv={() => exportCsv(d6?.slowestCategories ?? [], "tickets-slowest")}
                onExportPng={() => {}}
                onExportPdf={() => {}}
              />
            </div>
            {d6Loading ? (
              <div className={styles.tableMsg}>Загрузка…</div>
            ) : !d6?.slowestCategories.length ? (
              <div className={styles.tableMsg}>Нет данных</div>
            ) : (
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Категория</th>
                    <th>Ср. TTR (мин)</th>
                  </tr>
                </thead>
                <tbody>
                  {d6.slowestCategories.map((row) => (
                    <tr key={row.category}>
                      <td style={{ color: "#facc15" }}>{row.category}</td>
                      <td>{row.avgTtrMin.toFixed(0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className={styles.keywordsCard}>
            <div className={styles.keywordsHeader}>
              <h4 className={styles.keywordsCardTitle}>Аномалии (Z-score)</h4>
              <ExportToolbar
                onExportCsv={() => exportCsv(d6?.anomalies ?? [], "tickets-anomalies")}
                onExportPng={() => {}}
                onExportPdf={() => {}}
              />
            </div>
            {d6Loading ? (
              <div className={styles.tableMsg}>Загрузка…</div>
            ) : d6Error ? (
              <div className={styles.tableMsg}>Ошибка загрузки</div>
            ) : !d6?.anomalies.length ? (
              <div className={styles.tableMsg}>Аномалий не обнаружено</div>
            ) : (
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Категория</th>
                    <th>Продукт</th>
                    <th>48ч</th>
                    <th>Среднее</th>
                    <th>Z</th>
                  </tr>
                </thead>
                <tbody>
                  {d6.anomalies.map((a, i) => (
                    <tr key={i}>
                      <td style={{ color: "#f87171" }}>{a.category}</td>
                      <td>{a.product}</td>
                      <td>{a.count48h}</td>
                      <td>{a.rollingAvg.toFixed(1)}</td>
                      <td style={{ color: Math.abs(a.zScore) > 2 ? "#f87171" : "#facc15" }}>
                        {a.zScore.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </section>

      {/* Прогноз */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>Прогноз обращений на 7 дней</h3>
        <FilterBar
          filters={forecast.filters}
          onChange={forecast.updateFilters}
          onReset={forecast.resetFilters}
          onSave={forecast.saveConfig}
          hideDates
          hidePriority
        />

        <ChartContainer
          title="Прогноз (скользящее среднее ± 1σ)"
          isLoading={fcLoading}
          error={fcError}
          containerRef={forecastRef}
        >
          <div className={styles.chartWithExport}>
            <ExportToolbar
              onExportCsv={() => exportCsv(forecastData?.forecast ?? [], "tickets-forecast")}
              onExportPng={() => handleExportSvg(forecastRef, "tickets-forecast")}
              onExportPdf={() => forecastRef.current && exportPdf(forecastRef.current, "Прогноз обращений")}
            />
            {!fcLoading && !forecastData?.forecast.length ? (
              <div className={styles.tableMsg}>Недостаточно данных для прогноза</div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={forecastData?.forecast ?? []} margin={{ left: 0, right: 16, top: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" tick={{ fill: "#888", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#888", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: "#1e1b2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
                    labelStyle={{ color: "#fff" }}
                  />
                  <Legend formatter={(value) => <span style={{ color: "#aaa", fontSize: 12 }}>{value}</span>} />
                  <Line type="monotone" dataKey="predictedCount" name="Прогноз" stroke="#7c5cff" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="upperBound" name="Верх. граница" stroke="#c4b5fd" strokeWidth={1} strokeDasharray="4 4" dot={false} />
                  <Line type="monotone" dataKey="lowerBound" name="Ниж. граница" stroke="#c4b5fd" strokeWidth={1} strokeDasharray="4 4" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </ChartContainer>
      </section>
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
  if (isLoading) return <div className={styles.tableMsg}>Загрузка…</div>
  if (!data.length) return <div className={styles.tableMsg}>Нет данных</div>
  return (
    <table className={styles.table}>
      <thead>
        <tr>
          <th>Слово / категория</th>
          <th>Количество</th>
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
