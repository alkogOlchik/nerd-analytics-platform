import { useState } from "react"
import { AlertTriangle, Lightbulb, ClipboardList, User2, LogOut, Settings, User } from "lucide-react"
import styles from "./styles.module.scss"
import { Sidebar, PromptCard, QuickActionCard, FAQItem } from "modules"
import clsx from "clsx"
import { HelpCard } from "shared/ui/HelpCard"
import { Link } from "react-router-dom"
import { routes } from "shared/utils/routes"

export const MainScreen = () => {
  const [promptValue, setPromptValue] = useState("")
  const [isAvatarMenuOpen, setIsAvatarMenuOpen] = useState(false)

  return (
    <div className={styles.page}>
      <div className={clsx(styles.blob, styles.blob1)} />
      <div className={clsx(styles.blob, styles.blob3)} />
      <Sidebar onSelect={(id) => console.log(id)} />

      <main className={styles.main}>
        <div className={styles.logo}>
          <p className={styles.logo__text}>Привет, Алексей</p>
          <div
            className={styles.logo__avatar}
            onClick={() => setIsAvatarMenuOpen(!isAvatarMenuOpen)}
            role="button"
            tabIndex={0}
          >
            <User2 size={30} />
            {isAvatarMenuOpen && (
              <div className={styles.avatarDropdown}>
                <div className={styles.dropdownHeader}>
                  <div className={styles.avatarLarge}>
                    <User2 size={40} />
                  </div>
                  <div>
                    <p className={styles.fullName}>Алексей Иванов</p>
                    <p className={styles.email}>alex@example.com</p>
                  </div>
                </div>

                <div className={styles.dropdownDivider} />

                <Link to={routes.profile} className={styles.dropdownLink}>
                  <User size={18} />
                  <span>Профиль</span>
                </Link>

                <Link to={routes.profile} className={styles.dropdownLink}>
                  <Settings size={18} />
                  <span>Настройки</span>
                </Link>

                <div className={styles.dropdownDivider} />

                <button className={styles.logoutButton}>
                  <LogOut size={18} />
                  <span>Выйти</span>
                </button>
              </div>
            )}
          </div>
        </div>

        <section className={clsx(styles.helloSection, styles.section)}>

          <div className={styles.helloLeftContent}>
            <div className={styles.hero}>
              <h1 className={styles.title}>
                Привет! Я ваш <span className={styles.title_decorated}>AI-помощник</span> 👋
              </h1>

              <p className={styles.subtitle}>Опишите проблему, и я помогу найти решение.</p>
            </div>

            <PromptCard
              value={promptValue}
              onChange={setPromptValue}
              onSubmit={() => console.log("submit", promptValue)}
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
