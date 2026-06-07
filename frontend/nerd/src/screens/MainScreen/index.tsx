import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { AlertTriangle, Lightbulb } from "lucide-react"
import styles from "./styles.module.scss"
import { Sidebar, PromptCard, QuickActionCard, FAQItem, UserMenu } from "modules"
import clsx from "clsx"
import { HelpCard } from "shared/ui/HelpCard"
import { routes } from "shared/utils/routes"

export const MainScreen = () => {
  const [promptValue, setPromptValue] = useState("")
  const navigate = useNavigate()

  const handlePromptSubmit = () => {
    if (promptValue.trim()) {
      navigate(routes.assistant, { state: { initialMessage: promptValue } })
    }
  }

  return (
    <div className={styles.page}>
      <div className={clsx(styles.blob, styles.blob1)} />
      <div className={clsx(styles.blob, styles.blob3)} />
      <Sidebar onSelect={(id) => console.log(id)} />

      <main className={styles.main}>
        <div className={styles.mainHeader}>
          <UserMenu />
        </div>

        <section className={clsx(styles.helloSection, styles.section)}>
          <div className={styles.helloLeftContent}>
            <div className={styles.hero}>
              <h1 className={styles.title}>
                Привет! Я ваш <span className={styles.title_decorated}>AI-помощник</span> 👋
              </h1>
            </div>

            <PromptCard
              value={promptValue}
              onChange={setPromptValue}
              onSubmit={handlePromptSubmit}
            />
          </div>

          <div className={styles.helpCardWrapper}>
            <HelpCard />
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Быстрые действия</h2>

          <div className={styles.actionsGrid}>
            <QuickActionCard
              title="Проблема с сайтом Nerd Analytics"
              description="Создать новое обращение по этому сайту"
              icon={AlertTriangle}
              onClick={() => navigate(routes.createTicket)}
            />
            <QuickActionCard
              title="Оставить отзыв о Nerd Analytics"
              description="Поделитесь своим мнением об этом сайте"
              icon={Lightbulb}
              onClick={() => navigate(routes.feedback)}
            />
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Популярные проблемы</h2>

          <div className={styles.faqList}>
            <FAQItem question="Как подключить новый источник данных?" category="Analytics" />
            <FAQItem question="Почему не отображаются данные в отчётах?" category="Dashboard" />
            <FAQItem question="Как настроить уведомления?" category="All Products" />
          </div>
        </section>
      </main>
    </div>
  )
}
