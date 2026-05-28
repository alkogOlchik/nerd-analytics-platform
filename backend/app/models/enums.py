import enum


class Gender(str, enum.Enum):
    male = "male"
    female = "female"


class EmployeeStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class TicketProduct(str, enum.Enum):
    web = "веб-сервис"
    payment = "платёжный сервис"
    mobile = "мобильное приложение"
    api = "API интеграция"
    cabinet = "личный кабинет"
    analytics_module = "аналитический модуль"


class TicketCategory(str, enum.Enum):
    """Категории для тикетов (ai_suggested_category / final_category)."""

    technical = "технический сбой"
    payment = "вопрос по оплате"
    documents = "запрос документов"
    complaint = "жалоба на сервис"
    consultation = "консультация"
    data_error = "ошибка в данных"
    refund = "запрос возврата"
    access = "проблема с доступом"


# alias для обратной совместимости в коде
TicketType = TicketCategory


class ReviewCategory(str, enum.Enum):
    """Категории для отзывов (ai_suggested_category / final_category)."""

    speed = "скорость решения"
    answer_quality = "качество ответа"
    politeness = "вежливость"
    competence = "техническая компетентность"
    overall = "общее впечатление"


class TicketStatus(str, enum.Enum):
    accepted = "принято"
    in_progress = "в_работе"
    needs_info = "требуется_информация"
    dev_handoff = "передано_разработчикам"
    fixed = "исправлено"
    closed = "закрыто"
    rejected = "отклонено"


class EmployeeRole(str, enum.Enum):
    super_admin = "super_admin"
    product_owner = "product_owner"
    analyst = "analyst"
    operator = "operator"


ALLOWED_TICKET_STATUSES = {s.value for s in TicketStatus}


class TicketPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ChatRole(str, enum.Enum):
    client = "client"
    ai = "ai"
    admin = "admin"


class Sentiment(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class NotificationType(str, enum.Enum):
    email = "email"
    push = "push"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class UserRole(str, enum.Enum):
    client = "client"
    employee = "employee"
