import { Mail, MapPin, Cake, User, AtSign, Shield, Calendar, Settings } from "lucide-react"
import { Link } from "react-router-dom"
import type { ReactNode } from "react"
import styles from "./styles.module.scss"
import type { ProfileCardProps } from "./types"
import { useProfileCard } from "./useLogic"
import { routes } from "shared/utils/routes"

interface FieldProps {
  icon: ReactNode
  label: string
  value: string
}

const ProfileField = ({ icon, label, value }: FieldProps) => (
  <div className={styles.field}>
    <span className={styles.fieldIcon}>{icon}</span>
    <div className={styles.fieldContent}>
      <span className={styles.fieldLabel}>{label}</span>
      <span className={styles.fieldValue}>{value}</span>
    </div>
  </div>
)

export const ProfileCard = ({ profile, isLoading }: ProfileCardProps) => {
  if (isLoading || !profile) {
    return (
      <div className={styles.card}>
        <div className={styles.skeleton}>
          <div className={styles.skeletonAvatar} />
          <div className={styles.skeletonLines}>
            <div className={styles.skeletonLine} style={{ width: "60%" }} />
            <div className={styles.skeletonLine} style={{ width: "40%" }} />
          </div>
        </div>
      </div>
    )
  }

  const { initials, displayName, roleLabel, genderLabel, memberSince, registeredAt, ageLabel } =
    useProfileCard(profile)

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.avatar}>{initials}</div>
        <div className={styles.headerInfo}>
          <h2 className={styles.name}>{displayName}</h2>
          <p className={styles.username}>@{profile.authUsername}</p>
          <div className={styles.meta}>
            <span className={styles.roleBadge}>{roleLabel}</span>
            {memberSince && (
              <>
                <span className={styles.metaSeparator}>·</span>
                <span className={styles.memberSince}>Участник с {memberSince}</span>
              </>
            )}
          </div>
        </div>
      </div>

      <div className={styles.divider} />

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Личные данные</h3>

        {profile.email && (
          <div className={styles.emailRow}>
            <ProfileField icon={<Mail size={16} />} label="Email" value={profile.email} />
          </div>
        )}

        {profile.hasLocalData ? (
          <div className={styles.fieldsGrid}>
            {profile.fullName && (
              <ProfileField icon={<User size={16} />} label="Полное имя" value={profile.fullName} />
            )}
            {profile.city && (
              <ProfileField icon={<MapPin size={16} />} label="Город" value={profile.city} />
            )}
            {ageLabel && (
              <ProfileField icon={<Cake size={16} />} label="Возраст" value={ageLabel} />
            )}
            {genderLabel && (
              <ProfileField icon={<User size={16} />} label="Пол" value={genderLabel} />
            )}
          </div>
        ) : (
          <Link to={routes.settings} className={styles.hint}>
            <Settings size={16} />
            <span>Добавьте данные в настройках</span>
          </Link>
        )}
      </div>

      <div className={styles.divider} />

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>Данные аккаунта</h3>
        <div className={styles.fieldsGrid}>
          <ProfileField icon={<AtSign size={16} />} label="Логин" value={profile.username ?? profile.authUsername} />
          <ProfileField icon={<Shield size={16} />} label="Роль" value={roleLabel} />
          {registeredAt && (
            <ProfileField
              icon={<Calendar size={16} />}
              label="Дата регистрации"
              value={registeredAt}
            />
          )}
        </div>
      </div>
    </div>
  )
}
