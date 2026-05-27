import { AlertTriangle, Lightbulb, ClipboardList, User2 } from "lucide-react"
import styles from "./styles.module.scss"
import { Sidebar, PromptCard, QuickActionCard, FAQItem } from "modules"
import clsx from "clsx"
import { HelpCard } from "shared/ui/HelpCard"

export const MainScreen = () => {
  return (
    <div className={styles.page}>
      <div className={clsx(styles.blob, styles.blob1)} />
      <div className={clsx(styles.blob, styles.blob3)} />
      <Sidebar onSelect={(id) => console.log(id)} />

      <main className={styles.main}>
        <div className={styles.logo}>
          <p className={styles.logo__text}>Привет, Алексей</p>
          <div className={styles.logo__avatar}>
            <User2 size={30} />
          </div>
        </div>

        <section className={styles.helloSection}>

          <div>
            <div className={styles.hero}>
              <h1 className={styles.title}>
                Привет! Я ваш <span className={styles.title_decorated}>AI-помощник</span> 👋
              </h1>

              <p className={styles.subtitle}>Опишите проблему, и я помогу найти решение.</p>
            </div>

            <PromptCard
              value=""
              onChange={console.log}
              onSubmit={() => console.log("submit")}
            />
          </div>

          <HelpCard />

        </section>


        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Быстрые действия</h2>

          <div className={styles.actionsGrid}>
            <QuickActionCard
              title="Сообщить о проблеме"
              description="Создать новое обращение"
              icon={AlertTriangle}
            />

            <QuickActionCard
              title="Предложить улучшение"
              description="Отправить идею"
              icon={Lightbulb}
            />

            <QuickActionCard
              title="Проверить статус"
              description="Мои обращения"
              icon={ClipboardList}
            />
          </div>
        </section>
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Популярные проблемы</h2>

          <div className={styles.faqList}>
            <FAQItem
              question="Как подключить новый источник данных?"
              category="Analytics"
            />

            <FAQItem
              question="Почему не отображаются данные в отчётах?"
              category="Dashboard"
            />

            <FAQItem
              question="Как настроить уведомления?"
              category="All Products"
            />
          </div>
        </section>
      </main>
    </div>
  )
}
