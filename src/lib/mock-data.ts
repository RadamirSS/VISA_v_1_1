import { ApplicationRecord, ApplicationTimelineStep, ClientProfile, DemoState, DocumentItem, LeadFormValues, VisaFormData } from "@/lib/types";

export const initialLeadValues: LeadFormValues = {
  fullName: "",
  phone: "",
  telegram: "",
  email: "",
  citizenship: "Россия",
  location: "",
  schengenCountry: "Италия",
  purpose: "Туризм",
  travelDates: "",
  applicantsCount: "1",
  previousSchengen: "Нет",
  passportValidity: "",
  comment: "",
  consent: false
};

export const emptyProfile: ClientProfile = {
  password: "",
  phone: "",
  address: "",
  residenceCountry: "",
  residencePermit: "",
  emergencyContact: ""
};

export const emptyVisaForm: VisaFormData = {
  surname: "",
  givenName: "",
  previousNames: "",
  birthDate: "",
  birthPlace: "",
  birthCountry: "",
  nationality: "Россия",
  nationalityAtBirth: "Россия",
  gender: "",
  maritalStatus: "",
  minorDetails: "",
  passportNumber: "",
  passportIssueDate: "",
  passportExpiryDate: "",
  passportAuthority: "",
  passportType: "Заграничный паспорт",
  homeAddress: "",
  email: "",
  phone: "",
  currentResidence: "",
  residencePermitFields: "",
  occupation: "",
  employer: "",
  fundsSource: "",
  mainDestination: "",
  firstEntry: "",
  travelPurpose: "",
  arrivalDate: "",
  departureDate: "",
  entriesRequested: "",
  hostInfo: "",
  itineraryNotes: "",
  previousVisas: "",
  fingerprintsCollected: "unknown",
  previousRefusals: "",
  refusalNotes: "",
  expensesCoveredBy: "",
  accommodationPrepaid: "",
  transportPrepaid: "",
  otherSupport: "",
  dataConsent: false,
  accuracyConsent: false,
  authorityDisclaimer: false
};

export const timelineSteps: ApplicationTimelineStep[] = [
  { key: "lead_submitted", title: "Заявка отправлена", description: "Первичный запрос получен командой." },
  { key: "manager_review", title: "Проверка менеджером", description: "Менеджер уточняет направление и кейс." },
  { key: "approved", title: "Одобрено для подготовки", description: "Открыт доступ в личный кабинет." },
  { key: "profile_completed", title: "Профиль заполнен", description: "Контактные данные и адрес заполнены." },
  { key: "forms_completed", title: "Анкеты заполнены", description: "Основные визовые формы готовы к проверке." },
  { key: "documents_uploaded", title: "Документы загружены", description: "Загружены метаданные по документам." },
  { key: "documents_review", title: "Проверка документов", description: "Менеджер проверяет комплектность." },
  { key: "ready_for_appointment", title: "Готово к записи", description: "Кейс готов к поиску слота." },
  { key: "appointment_booking", title: "Запись в консульство", description: "Интеграция пока работает в демо-режиме." },
  { key: "payment", title: "Оплата", description: "Платежный провайдер будет подключен позже." },
  { key: "appointment_confirmed", title: "Подтверждение записи", description: "Финальное подтверждение появится после интеграции." }
];

export const defaultDocuments = (): DocumentItem[] => [
  { id: "passport", type: "passport", title: "Скан загранпаспорта", required: true, guidance: "PDF/JPG, до 10 МБ", status: "missing", managerComment: "", clientComment: "" },
  { id: "old-visas", type: "old-visas", title: "Предыдущие паспорта и визы", required: false, guidance: "PDF/JPG, до 10 МБ", status: "missing", managerComment: "", clientComment: "" },
  { id: "photo", type: "photo", title: "Фотография", required: true, guidance: "JPEG, светлый фон, до 5 МБ", status: "missing", managerComment: "", clientComment: "" },
  { id: "insurance", type: "insurance", title: "Страховка", required: true, guidance: "PDF, покрытие по правилам Шенгена", status: "missing", managerComment: "", clientComment: "" },
  { id: "flight", type: "flight", title: "Бронь перелета / маршрут", required: true, guidance: "PDF, без оплаты при необходимости", status: "missing", managerComment: "", clientComment: "" },
  { id: "hotel", type: "hotel", title: "Бронь жилья", required: true, guidance: "PDF/ссылка, до 10 МБ", status: "missing", managerComment: "", clientComment: "" },
  { id: "bank", type: "bank", title: "Выписка из банка", required: true, guidance: "PDF, свежая выписка", status: "missing", managerComment: "", clientComment: "" },
  { id: "employment", type: "employment", title: "Справка с работы / документы бизнеса", required: true, guidance: "PDF, актуальная дата", status: "missing", managerComment: "", clientComment: "" },
  { id: "tax", type: "tax", title: "Налоговые / доходные документы", required: false, guidance: "PDF, если применимо", status: "missing", managerComment: "", clientComment: "" },
  { id: "travel-plan", type: "travel-plan", title: "План поездки", required: false, guidance: "Текст или PDF", status: "missing", managerComment: "", clientComment: "" },
  { id: "invitation", type: "invitation", title: "Приглашение", required: false, guidance: "PDF, если применимо", status: "missing", managerComment: "", clientComment: "" },
  { id: "family", type: "family", title: "Семейные документы", required: false, guidance: "PDF/JPG, если применимо", status: "missing", managerComment: "", clientComment: "" },
  { id: "country-specific", type: "country-specific", title: "Дополнительные документы по стране", required: false, guidance: "PDF/JPG, по инструкции менеджера", status: "missing", managerComment: "", clientComment: "" }
];

export const seedDemoState = (): DemoState => {
  const leadId = "lead-demo-1";
  const inviteToken = "INVITE-DEMO-2026";
  const applicationId = "app-demo-1";
  const application: ApplicationRecord = {
    id: applicationId,
    leadId,
    inviteToken,
    registered: false,
    managerStatus: "approved",
    fullName: "Демо Клиент",
    email: "demo@example.com",
    visaDirection: "Италия",
    profile: emptyProfile,
    visaForm: { ...emptyVisaForm, email: "demo@example.com", mainDestination: "Италия", firstEntry: "Италия", travelPurpose: "Туризм" },
    documents: defaultDocuments(),
    timelineCompletedKeys: ["lead_submitted", "manager_review", "approved"]
  };

  return {
    leads: [
      {
        id: leadId,
        createdAt: new Date("2026-06-01T09:00:00.000Z").toISOString(),
        status: "approved",
        approvalNote: "Демо-кейс для показа клиентского пути.",
        inviteToken,
        values: {
          fullName: "Демо Клиент",
          phone: "+7 900 123-45-67",
          telegram: "@demo_client",
          email: "demo@example.com",
          citizenship: "Россия",
          location: "Белград, Сербия",
          schengenCountry: "Италия",
          purpose: "Туризм",
          travelDates: "Сентябрь 2026",
          applicantsCount: "1",
          previousSchengen: "Да",
          passportValidity: "До 2029-10-01",
          comment: "Хочу видеть весь путь в демо-режиме.",
          consent: true
        }
      }
    ],
    applications: [application],
    session: {
      applicationId: null
    }
  };
};
