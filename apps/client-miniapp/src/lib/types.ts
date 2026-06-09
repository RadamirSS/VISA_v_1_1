export type ApplicantStatus = "draft" | "incomplete" | "completed" | "needs_review" | "approved_by_manager";

export type ApplicantProfile = {
  id: string;
  user_id: string;
  telegram_id: number;
  case_id?: string | null;
  position: number;
  role?: string | null;
  status: ApplicantStatus;
  completion_percent: number;
  last_name_latin?: string | null;
  first_name_latin?: string | null;
  last_name_cyrillic?: string | null;
  first_name_cyrillic?: string | null;
  patronymic?: string | null;
  birth_date?: string | null;
  birth_place?: string | null;
  citizenship?: string | null;
  gender?: string | null;
  marital_status?: string | null;
  phone?: string | null;
  email?: string | null;
  residence_country?: string | null;
  residence_city?: string | null;
  residence_address?: string | null;
  postal_code?: string | null;
  passport_number?: string | null;
  passport_issue_date?: string | null;
  passport_expiry_date?: string | null;
  passport_issuing_authority?: string | null;
  passport_issuing_country?: string | null;
  desired_country_code?: string | null;
  desired_country_name_ru?: string | null;
  travel_purpose?: string | null;
  approximate_travel_dates?: string | null;
  entries_count?: string | null;
  preferred_submission_city?: string | null;
  created_at: string;
  updated_at: string;
};

export type VisaCase = {
  id: string;
  user_id: string;
  telegram_id: number;
  access_key_id?: string | null;
  access_key_code?: string | null;
  status: string;
  applicants_count: number;
  desired_country_code?: string | null;
  desired_country_name_ru?: string | null;
  preferred_submission_city?: string | null;
  submission_provider?: string | null;
  submission_provider_type?: string | null;
  submission_jurisdiction?: string | null;
  submission_verification_status?: string | null;
  travel_purpose?: string | null;
  approximate_travel_start_date?: string | null;
  approximate_travel_end_date?: string | null;
  client_comment?: string | null;
  submitted_at?: string | null;
  manager_reviewed_at?: string | null;
  selected_slot_option_id?: string | null;
  selected_appointment_date?: string | null;
  selected_appointment_time?: string | null;
  selected_appointment_city?: string | null;
  selected_appointment_provider?: string | null;
  appointment_confirmed_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type MeResponse = {
  telegram_id: number;
  user_id: string;
  username?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  has_active_access: boolean;
  active_access_key_code?: string | null;
  current_case_status?: string | null;
  has_case: boolean;
};

export type ApplicantPayload = Partial<Omit<ApplicantProfile, "id" | "user_id" | "telegram_id" | "position" | "status" | "completion_percent" | "created_at" | "updated_at">>;

export type CountryOption = {
  code: string;
  slug: string;
  name_ru: string;
  suits_for_ru: string;
};

export type ConsulateOption = {
  country_code: string;
  country_name_ru: string;
  city: string;
  provider: string;
  type: string;
  jurisdiction: string;
  status: string;
  verification_status: string;
  last_checked_at: string;
  source_note: string;
};

export type CasePayload = {
  desired_country_code?: string | null;
  desired_country_name_ru?: string | null;
  preferred_submission_city?: string | null;
  submission_provider?: string | null;
  travel_purpose?: string | null;
  approximate_travel_start_date?: string | null;
  approximate_travel_end_date?: string | null;
  client_comment?: string | null;
};

export type CreateCaseResponse = {
  case: VisaCase;
  incomplete_applicants: string[];
};

export type SubmitCaseResponse = {
  case: VisaCase;
  incomplete_applicants: ApplicantProfile[];
};

export type SlotOption = {
  id: string;
  offer_id: string;
  case_id: string;
  option_date: string;
  option_time: string;
  city?: string | null;
  provider?: string | null;
  address?: string | null;
  comment?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type SlotOffer = {
  id: string;
  case_id: string;
  created_by_admin_id: number;
  status: string;
  message?: string | null;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
  options: SlotOption[];
};

export type TimelineStepState = "done" | "current" | "locked" | "warning";

export type TimelineStep = {
  key: string;
  label: string;
  state: TimelineStepState;
};

export type NextAction = {
  type: string;
  label: string;
  href: string;
};

export type CaseTimelineResponse = {
  status: string;
  status_label: string;
  steps: TimelineStep[];
};

export type CabinetSummary = {
  user: {
    telegram_id: number;
    first_name?: string | null;
    username?: string | null;
  };
  access: {
    active: boolean;
    status_label: string;
  };
  case?: {
    id: string;
    public_number: string;
    status: string;
    status_label: string;
    desired_country_name_ru?: string | null;
    preferred_submission_city?: string | null;
    submission_provider?: string | null;
    applicants_count: number;
    next_action: NextAction;
  } | null;
  next_action?: NextAction | null;
  applicants: {
    total: number;
    completed: number;
    incomplete: number;
  };
  appointment: {
    has_options: boolean;
    selected: {
      date?: string | null;
      time?: string | null;
      city?: string | null;
      provider?: string | null;
    } | null;
    confirmed: {
      date?: string | null;
      time?: string | null;
      city?: string | null;
      provider?: string | null;
    } | null;
  };
  documents?: CabinetDocumentsSummary | null;
};

export type CabinetDocumentsSummary = {
  has_items: boolean;
  client_pending: number;
  client_uploaded: number;
  agency_in_progress: number;
  agency_ready: number;
  agency_shared: number;
};

export type DocumentItem = {
  id: string;
  source_type: "client_required" | "agency_prepared";
  category: string;
  title: string;
  description?: string | null;
  status: string;
  status_label: string;
  required: boolean;
  manager_comment?: string | null;
  client_comment?: string | null;
  can_upload: boolean;
  can_download: boolean;
  has_file: boolean;
  uploads_enabled: boolean;
  transferred_separately: boolean;
};

export type DocumentsListResponse = {
  items: DocumentItem[];
  uploads_enabled: boolean;
};
