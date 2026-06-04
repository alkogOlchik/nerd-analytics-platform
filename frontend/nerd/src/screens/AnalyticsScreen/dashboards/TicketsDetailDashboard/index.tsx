import { useReviewsKeywords } from "domain/Analytics"
import { useAnalyticsFilters } from "../../hooks/useAnalyticsFilters"
import { FilterBar } from "../../components/FilterBar"
import { ComingSoon } from "../../components/ComingSoon"
import { ExportToolbar } from "../../components/ExportToolbar"
import { exportCsv } from "shared/utils/exportAnalytics"
import styles from "./styles.module.scss"

export const TicketsDetailDashboard = () => {
  const analysis = useAnalyticsFilters("tickets-analysis")
  const forecast = useAnalyticsFilters("tickets-forecast")

  const { data: keywords, isLoading: kwLoading } = useReviewsKeywords(analysis.filters)

  const allKeywords = [
    ...(keywords?.keywordsPositive ?? []).map((k) => ({ ...k, type: "positive" })),
    ...(keywords?.keywordsNegative ?? []).map((k) => ({ ...k, type: "negative" })),
  ]

  return (
    <div className={styles.dashboard}>
      {/* === Блок анализа === */}
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
              <h4 className={styles.keywordsCardTitle}>Позитивные ключевые слова</h4>
              <ExportToolbar
                onExportCsv={() => exportCsv(keywords?.keywordsPositive ?? [], "tickets-keywords-positive")}
                onExportPng={() => {}}
                onExportPdf={() => {}}
              />
            </div>
            <KeywordsTable data={keywords?.keywordsPositive ?? []} isLoading={kwLoading} accentColor="#4ade80" />
          </div>

          <div className={styles.keywordsCard}>
            <div className={styles.keywordsHeader}>
              <h4 className={styles.keywordsCardTitle}>Негативные ключевые слова</h4>
              <ExportToolbar
                onExportCsv={() => exportCsv(keywords?.keywordsNegative ?? [], "tickets-keywords-negative")}
                onExportPng={() => {}}
                onExportPdf={() => {}}
              />
            </div>
            <KeywordsTable data={keywords?.keywordsNegative ?? []} isLoading={kwLoading} accentColor="#f87171" />
          </div>
        </div>

        <div className={styles.keywordsCard}>
          <div className={styles.keywordsHeader}>
            <h4 className={styles.keywordsCardTitle}>Поиск аномалий</h4>
          </div>
          <ComingSoon
            title="Обнаружение аномалий"
            description="Линейный график с выделением аномальных точек появится после подключения соответствующего эндпоинта."
          />
        </div>
      </section>

      {/* === Блок прогноза (независимые фильтры) === */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>Прогноз обращений</h3>
        <FilterBar
          filters={forecast.filters}
          onChange={forecast.updateFilters}
          onReset={forecast.resetFilters}
          onSave={forecast.saveConfig}
          hideDates
        />

        <div className={styles.keywordsCard}>
          <div className={styles.keywordsHeader}>
            <h4 className={styles.keywordsCardTitle}>Прогноз на 7 дней</h4>
          </div>
          <ComingSoon
            title="Прогноз числа обращений"
            description="Линейный график с прогнозными значениями на 7 дней появится после подключения соответствующего эндпоинта."
          />
        </div>

        {allKeywords.length > 0 && (
          <div className={styles.exportRow}>
            <ExportToolbar
              onExportCsv={() => exportCsv(allKeywords, "tickets-all-keywords")}
              onExportPng={() => {}}
              onExportPdf={() => {}}
            />
          </div>
        )}
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
