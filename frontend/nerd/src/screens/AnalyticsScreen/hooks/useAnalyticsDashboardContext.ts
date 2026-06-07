import {
  useTicketSummary,
  useTicketTimeline,
  useSla,
  useAdminWorkload,
  useAdminSla,
  useAiAccuracy,
  useAiEfficiency,
  useUsersDemographics,
  useUsersRetention,
  useReviewsSummary,
  useReviewsKeywords,
  useReviewsDynamics,
  useDashboard6Tickets,
  useTicketForecast,
} from "domain/Analytics"

type DashboardId = "overview" | "ai" | "admins" | "users" | "reviews" | "tickets"

const fmt = (n: number | null | undefined, unit = "") =>
  n == null ? "н/д" : `${n}${unit}`

const list = (items: { key: string; count: number }[] | undefined) =>
  items?.map((i) => `${i.key}: ${i.count}`).join(", ") ?? "нет данных"

export const useAnalyticsDashboardContext = (dashboard: DashboardId): string => {
  // All hooks always called (Rules of Hooks). TanStack Query deduplicates
  // these requests with the dashboard component's own calls (same query key).
  const summary = useTicketSummary()
  const timeline = useTicketTimeline()
  const sla = useSla()
  const adminWorkload = useAdminWorkload()
  const adminSla = useAdminSla()
  const aiAccuracy = useAiAccuracy()
  const aiEfficiency = useAiEfficiency()
  const usersDemographics = useUsersDemographics()
  const usersRetention = useUsersRetention()
  const reviewsSummary = useReviewsSummary()
  const reviewsKeywords = useReviewsKeywords()
  const reviewsDynamics = useReviewsDynamics()
  const d6 = useDashboard6Tickets()
  const forecastData = useTicketForecast({})

  switch (dashboard) {
    case "overview": {
      const s = summary.data
      const tl = timeline.data
      const lines = [
        "=== Дашборд: Сводная ===",
        `Тикеты по статусам: ${list(s?.byStatus)}`,
        `Тикеты по продуктам: ${list(s?.byProduct)}`,
        `Тикеты по категориям: ${list(s?.byCategory)}`,
        `Динамика (последние точки): ${
          tl?.items
            .slice(-7)
            .map((i) => `${i.date}: ${i.count}`)
            .join(", ") ?? "нет данных"
        }`,
      ]
      return lines.join("\n")
    }

    case "admins": {
      const s = sla.data
      const wl = adminWorkload.data
      const asl = adminSla.data
      const lines = [
        "=== Дашборд: Администраторы ===",
        `SLA — всего: ${fmt(s?.total)}, соблюдено: ${fmt(s?.compliant)}, нарушено: ${fmt(s?.breached)}, соблюдение: ${fmt(s?.complianceRate, "%")}`,
        `Нагрузка по администраторам: ${
          wl?.items
            .map((i) => `${i.username} (открытых: ${i.openTickets}, закрытых: ${i.closedTickets})`)
            .join("; ") ?? "нет данных"
        }`,
        `SLA по приоритетам: ${
          asl?.byPriority
            .map((p) => `${p.priority} — TTFR: ${fmt(p.avgTtfr, "ч")}, TTR: ${fmt(p.avgTtr, "ч")}`)
            .join("; ") ?? "нет данных"
        }`,
        `Топ нарушений по категориям: ${list(asl?.topViolatedCategories)}`,
      ]
      return lines.join("\n")
    }

    case "ai": {
      const acc = aiAccuracy.data
      const eff = aiEfficiency.data
      const lines = [
        "=== Дашборд: ИИ ===",
        `Классификация — всего: ${fmt(acc?.totalClassified)}, изменено вручную: ${fmt(acc?.adminChanged)}, точность: ${fmt(acc?.accuracyRate, "%")}`,
        `Автоматически решено: ${fmt(eff?.autoResolved)} (${fmt(eff?.autoResolvedPct, "%")})`,
        `Эскалировано: ${fmt(eff?.escalated)}`,
        `Среднее сообщений до эскалации: ${fmt(eff?.avgMessagesBeforeEscalation)}`,
        `Топ категорий эскалации: ${list(eff?.topEscalatedCategories)}`,
        `Топ авторешённых категорий: ${list(eff?.topResolvedCategories)}`,
      ]
      return lines.join("\n")
    }

    case "users": {
      const dem = usersDemographics.data
      const ret = usersRetention.data
      const lines = [
        "=== Дашборд: Пользователи ===",
        `По полу: ${dem?.byGender.map((g) => `${g.key}: ${g.count}`).join(", ") ?? "нет данных"}`,
        `По возрасту: ${dem?.byAgeGroup.map((g) => `${g.key}: ${g.count}`).join(", ") ?? "нет данных"}`,
        `Топ городов: ${dem?.byCity.slice(0, 5).map((g) => `${g.key}: ${g.count}`).join(", ") ?? "нет данных"}`,
        `Удержание 7д: ${fmt(ret?.retention7dPct, "%")}, 14д: ${fmt(ret?.retention14dPct, "%")}, 30д: ${fmt(ret?.retention30dPct, "%")}`,
      ]
      return lines.join("\n")
    }

    case "reviews": {
      const rs = reviewsSummary.data
      const rk = reviewsKeywords.data
      const rd = reviewsDynamics.data
      const lines = [
        "=== Дашборд: Отзывы ===",
        `Средний рейтинг: ${fmt(rs?.averageRating)}, всего отзывов: ${fmt(rs?.totalReviews)}`,
        `Настроения: ${list(rs?.sentimentDistribution)}`,
        `Топ позитивных ключевых слов: ${rk?.keywordsPositive.slice(0, 5).map((k) => k.key).join(", ") ?? "нет данных"}`,
        `Топ негативных ключевых слов: ${rk?.keywordsNegative.slice(0, 5).map((k) => k.key).join(", ") ?? "нет данных"}`,
        `Динамика (последние точки): ${
          rd?.items
            .slice(-7)
            .map((i) => `${i.date}: +${i.positiveCount}/-${i.negativeCount}`)
            .join(", ") ?? "нет данных"
        }`,
      ]
      return lines.join("\n")
    }

    case "tickets": {
      const d = d6.data
      const fc = forecastData.data
      const lines = [
        "=== Дашборд: Тикеты (детально) ===",
        `Топ ключевых слов: ${d?.topKeywords.slice(0, 8).map((w) => `${w.word}(${w.count})`).join(", ") ?? "нет данных"}`,
        `Топ категорий: ${list(d?.topCategories)}`,
        `Аномалии: ${
          d?.anomalies.map((a) => `${a.category} — ${a.zScore != null ? `z=${a.zScore.toFixed(1)}` : "?"}`).join("; ") ?? "нет данных"
        }`,
        `Самые медленные категории: ${
          d?.slowestCategories.map((c) => `${c.category}: ${fmt(c.avgTtrMin, "мин")}`).join(", ") ?? "нет данных"
        }`,
        `Прогноз (след. точки): ${
          fc?.forecast
            .slice(0, 5)
            .map((f) => `${f.date}: ${f.predictedCount}`)
            .join(", ") ?? "нет данных"
        }`,
      ]
      return lines.join("\n")
    }

    default:
      return ""
  }
}
