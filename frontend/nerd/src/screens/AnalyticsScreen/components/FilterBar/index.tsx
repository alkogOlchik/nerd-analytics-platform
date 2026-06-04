import styles from "./styles.module.scss"
import type { AnalyticsFilters } from "data/repositories/Analytics"

interface FilterBarProps {
  filters: AnalyticsFilters
  onChange: (next: Partial<AnalyticsFilters>) => void
  onReset: () => void
  onSave: () => void
  hideDates?: boolean
}

export const FilterBar = ({ filters, onChange, onReset, onSave, hideDates }: FilterBarProps) => (
  <div className={styles.bar}>
    {!hideDates && (
      <>
        <label className={styles.field}>
          <span className={styles.fieldLabel}>С</span>
          <input
            type="date"
            className={styles.input}
            value={filters.from ?? ""}
            onChange={(e) => onChange({ from: e.target.value || undefined })}
          />
        </label>
        <label className={styles.field}>
          <span className={styles.fieldLabel}>По</span>
          <input
            type="date"
            className={styles.input}
            value={filters.to ?? ""}
            onChange={(e) => onChange({ to: e.target.value || undefined })}
          />
        </label>
      </>
    )}
    <label className={styles.field}>
      <span className={styles.fieldLabel}>Продукт</span>
      <input
        type="text"
        className={styles.input}
        placeholder="Все продукты"
        value={filters.product ?? ""}
        onChange={(e) => onChange({ product: e.target.value || undefined })}
      />
    </label>
    <label className={styles.field}>
      <span className={styles.fieldLabel}>Категория</span>
      <input
        type="text"
        className={styles.input}
        placeholder="Все категории"
        value={filters.category ?? ""}
        onChange={(e) => onChange({ category: e.target.value || undefined })}
      />
    </label>
    <div className={styles.actions}>
      <button className={styles.btnReset} onClick={onReset}>Сбросить</button>
      <button className={styles.btnSave} onClick={onSave}>Сохранить конфигурацию</button>
    </div>
  </div>
)
