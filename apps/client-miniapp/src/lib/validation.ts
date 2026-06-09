import type { ApplicantPayload } from "./types";

const requiredLabels: Record<keyof ApplicantPayload, string> = {
  last_name_latin: "Фамилия латиницей",
  first_name_latin: "Имя латиницей",
  last_name_cyrillic: "Фамилия кириллицей",
  first_name_cyrillic: "Имя кириллицей",
  patronymic: "Отчество",
  birth_date: "Дата рождения",
  birth_place: "Место рождения",
  citizenship: "Гражданство",
  gender: "Пол",
  marital_status: "Семейное положение",
  phone: "Телефон",
  email: "Email",
  residence_country: "Страна проживания",
  residence_city: "Город проживания",
  residence_address: "Адрес проживания",
  postal_code: "Почтовый индекс",
  passport_number: "Номер паспорта",
  passport_issue_date: "Дата выдачи паспорта",
  passport_expiry_date: "Срок действия паспорта",
  passport_issuing_authority: "Кем выдан паспорт",
  passport_issuing_country: "Страна выдачи паспорта",
  desired_country_code: "Страна поездки",
  desired_country_name_ru: "Страна поездки",
  travel_purpose: "Цель поездки",
  approximate_travel_dates: "Примерные даты поездки",
  entries_count: "Количество въездов",
  preferred_submission_city: "Предпочтительный город подачи",
  case_id: "Заявка",
  role: "Роль"
};

const requiredFields: Array<keyof ApplicantPayload> = [
  "last_name_latin",
  "first_name_latin",
  "last_name_cyrillic",
  "first_name_cyrillic",
  "birth_date",
  "birth_place",
  "citizenship",
  "phone",
  "residence_country",
  "residence_city",
  "residence_address",
  "passport_number",
  "passport_issue_date",
  "passport_expiry_date",
  "passport_issuing_country",
  "desired_country_code",
  "travel_purpose"
];

export function validateApplicant(payload: ApplicantPayload) {
  const errors: Partial<Record<keyof ApplicantPayload, string>> = {};
  for (const field of requiredFields) {
    if (!payload[field] || String(payload[field]).trim() === "") {
      errors[field] = `Поле «${requiredLabels[field]}» обязательно`;
    }
  }
  return errors;
}
