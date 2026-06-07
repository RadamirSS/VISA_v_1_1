"use client";

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { defaultDocuments, emptyProfile, emptyVisaForm, seedDemoState } from "@/lib/mock-data";
import { clamp, createId } from "@/lib/utils";
import { ApplicationRecord, DemoState, DocumentStatus, Lead, LeadFormValues, LeadStatus, VisaFormData } from "@/lib/types";

const STORAGE_KEY = "visa-v1-demo-state";

type DemoStoreValue = {
  state: DemoState;
  createLead: (payload: LeadFormValues) => Lead;
  updateLeadStatus: (leadId: string, status: LeadStatus) => void;
  registerWithInvite: (inviteToken: string, password: string) => { ok: boolean; message: string };
  loginMock: (email: string, password: string) => { ok: boolean; message: string };
  logout: () => void;
  getCurrentApplication: () => ApplicationRecord | null;
  updateProfile: (payload: ApplicationRecord["profile"]) => void;
  updateVisaForm: (payload: Partial<VisaFormData>) => void;
  updateDocumentMetadata: (
    documentId: string,
    payload: { fileName: string; fileType: string; fileSizeKb: number; clientComment: string }
  ) => void;
  updateDocumentStatus: (documentId: string, status: DocumentStatus) => void;
  getLeadById: (leadId: string) => Lead | undefined;
  getApplicationByInvite: (inviteToken: string) => ApplicationRecord | undefined;
  getProgress: (application: ApplicationRecord | null) => {
    profileCompletion: number;
    formCompletion: number;
    documentsCompletion: number;
    missingDocuments: number;
    totalCompletion: number;
  };
  placeholders: {
    searchAppointmentSlots: (query: string) => string[];
    bookAppointmentPlaceholder: () => string;
    createPaymentPlaceholder: () => string;
  };
};

const DemoStoreContext = createContext<DemoStoreValue | null>(null);

const getFilledFieldsPercent = (values: Record<string, unknown>) => {
  const entries = Object.entries(values);
  const filled = entries.filter(([key, value]) => {
    if (typeof value === "boolean") {
      return value;
    }

    if (key === "password") {
      return value;
    }

    return typeof value === "string" ? value.trim().length > 0 : Boolean(value);
  }).length;

  return clamp(Math.round((filled / entries.length) * 100));
};

export function DemoStoreProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DemoState>(seedDemoState);

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        setState(JSON.parse(saved) as DemoState);
      } catch {
        setState(seedDemoState());
      }
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const value = useMemo<DemoStoreValue>(() => {
    const getCurrentApplication = () =>
      state.applications.find((application) => application.id === state.session.applicationId) ?? null;

    const getLeadById = (leadId: string) => state.leads.find((lead) => lead.id === leadId);
    const getApplicationByInvite = (inviteToken: string) =>
      state.applications.find((application) => application.inviteToken === inviteToken);

    const createLead = (payload: LeadFormValues) => {
      const lead: Lead = {
        id: createId("lead"),
        createdAt: new Date().toISOString(),
        status: "new",
        values: payload
      };

      setState((current) => ({
        ...current,
        leads: [lead, ...current.leads]
      }));

      return lead;
    };

    const updateLeadStatus = (leadId: string, status: LeadStatus) => {
      setState((current) => {
        const lead = current.leads.find((entry) => entry.id === leadId);
        if (!lead) {
          return current;
        }

        const inviteToken = status === "approved" ? lead.inviteToken ?? `INV-${lead.id.toUpperCase()}` : lead.inviteToken;

        const existingApplication = current.applications.find((application) => application.leadId === leadId);
        const nextApplications =
          status === "approved"
            ? existingApplication
              ? current.applications.map((application) =>
                  application.leadId === leadId
                    ? {
                        ...application,
                        inviteToken: inviteToken!,
                        managerStatus: status
                      }
                    : application
                )
              : [
                  {
                    id: createId("app"),
                    leadId,
                    inviteToken: inviteToken!,
                    registered: false,
                    managerStatus: status,
                    fullName: lead.values.fullName,
                    email: lead.values.email,
                    visaDirection: lead.values.schengenCountry,
                    profile: { ...emptyProfile, phone: lead.values.phone },
                    visaForm: {
                      ...emptyVisaForm,
                      email: lead.values.email,
                      phone: lead.values.phone,
                      mainDestination: lead.values.schengenCountry,
                      firstEntry: lead.values.schengenCountry,
                      travelPurpose: lead.values.purpose
                    },
                    documents: defaultDocuments(),
                    timelineCompletedKeys: ["lead_submitted", "manager_review", "approved"]
                  },
                  ...current.applications
                ]
            : current.applications.map((application) =>
                application.leadId === leadId ? { ...application, managerStatus: status } : application
              );

        return {
          ...current,
          leads: current.leads.map((entry) =>
            entry.id === leadId
              ? {
                  ...entry,
                  status,
                  inviteToken,
                  approvalNote:
                    status === "approved"
                      ? "Заявка одобрена. Пользователь может зарегистрироваться в кабинете."
                      : entry.approvalNote
                }
              : entry
          ),
          applications: nextApplications
        };
      });
    };

    const registerWithInvite = (inviteToken: string, password: string) => {
      const application = state.applications.find((entry) => entry.inviteToken === inviteToken);

      if (!application) {
        return { ok: false, message: "Приглашение не найдено. Проверьте код доступа." };
      }

      setState((current) => ({
        ...current,
        applications: current.applications.map((entry) =>
          entry.inviteToken === inviteToken
            ? {
                ...entry,
                registered: true,
                profile: {
                  ...entry.profile,
                  password
                }
              }
            : entry
        ),
        session: {
          applicationId: application.id
        }
      }));

      return { ok: true, message: "Регистрация завершена. Доступ в кабинет открыт." };
    };

    const loginMock = (email: string, password: string) => {
      const application = state.applications.find((entry) => entry.email === email && entry.profile.password === password);

      if (!application) {
        return { ok: false, message: "Не удалось войти. Проверьте email, пароль и статус приглашения." };
      }

      setState((current) => ({
        ...current,
        session: {
          applicationId: application.id
        }
      }));

      return { ok: true, message: "Вход выполнен." };
    };

    const logout = () => {
      setState((current) => ({
        ...current,
        session: {
          applicationId: null
        }
      }));
    };

    const syncTimeline = (application: ApplicationRecord) => {
      const profileCompletion = getFilledFieldsPercent(application.profile);
      const formCompletion = getFilledFieldsPercent(application.visaForm);
      const uploadedDocuments = application.documents.filter((item) => item.status !== "missing").length;

      const next = new Set(["lead_submitted", "manager_review"]);
      if (application.managerStatus === "approved") {
        next.add("approved");
      }
      if (profileCompletion >= 70) {
        next.add("profile_completed");
      }
      if (formCompletion >= 70) {
        next.add("forms_completed");
      }
      if (uploadedDocuments >= 5) {
        next.add("documents_uploaded");
      }
      if (uploadedDocuments >= 8) {
        next.add("documents_review");
        next.add("ready_for_appointment");
      }

      return Array.from(next);
    };

    const updateProfile = (payload: ApplicationRecord["profile"]) => {
      setState((current) => ({
        ...current,
        applications: current.applications.map((entry) =>
          entry.id === current.session.applicationId
            ? {
                ...entry,
                profile: payload,
                timelineCompletedKeys: syncTimeline({ ...entry, profile: payload })
              }
            : entry
        )
      }));
    };

    const updateVisaForm = (payload: Partial<VisaFormData>) => {
      setState((current) => ({
        ...current,
        applications: current.applications.map((entry) =>
          entry.id === current.session.applicationId
            ? {
                ...entry,
                visaForm: {
                  ...entry.visaForm,
                  ...payload
                },
                timelineCompletedKeys: syncTimeline({
                  ...entry,
                  visaForm: {
                    ...entry.visaForm,
                    ...payload
                  }
                })
              }
            : entry
        )
      }));
    };

    const updateDocumentMetadata = (
      documentId: string,
      payload: { fileName: string; fileType: string; fileSizeKb: number; clientComment: string }
    ) => {
      setState((current) => ({
        ...current,
        applications: current.applications.map((entry) => {
          if (entry.id !== current.session.applicationId) {
            return entry;
          }

          const documents = entry.documents.map((item) =>
            item.id === documentId
              ? {
                  ...item,
                  ...payload,
                  uploadedAt: new Date().toISOString(),
                  status: "uploaded" as DocumentStatus
                }
              : item
          );

          return {
            ...entry,
            documents,
            timelineCompletedKeys: syncTimeline({
              ...entry,
              documents
            })
          };
        })
      }));
    };

    const updateDocumentStatus = (documentId: string, status: DocumentStatus) => {
      setState((current) => ({
        ...current,
        applications: current.applications.map((entry) => {
          if (entry.id !== current.session.applicationId) {
            return entry;
          }

          const documents = entry.documents.map((item) =>
            item.id === documentId
              ? {
                  ...item,
                  status
                }
              : item
          );

          return {
            ...entry,
            documents,
            timelineCompletedKeys: syncTimeline({
              ...entry,
              documents
            })
          };
        })
      }));
    };

    const getProgress = (application: ApplicationRecord | null) => {
      if (!application) {
        return {
          profileCompletion: 0,
          formCompletion: 0,
          documentsCompletion: 0,
          missingDocuments: 0,
          totalCompletion: 0
        };
      }

      const profileCompletion = getFilledFieldsPercent(application.profile);
      const formCompletion = getFilledFieldsPercent(application.visaForm);
      const readyDocuments = application.documents.filter((item) => item.status !== "missing").length;
      const documentsCompletion = clamp(Math.round((readyDocuments / application.documents.length) * 100));
      const missingDocuments = application.documents.filter((item) => item.required && item.status === "missing").length;
      const totalCompletion = clamp(Math.round((profileCompletion + formCompletion + documentsCompletion) / 3));

      return {
        profileCompletion,
        formCompletion,
        documentsCompletion,
        missingDocuments,
        totalCompletion
      };
    };

    return {
      state,
      createLead,
      updateLeadStatus,
      registerWithInvite,
      loginMock,
      logout,
      getCurrentApplication,
      updateProfile,
      updateVisaForm,
      updateDocumentMetadata,
      updateDocumentStatus,
      getLeadById,
      getApplicationByInvite,
      getProgress,
      placeholders: {
        searchAppointmentSlots: (query: string) =>
          query.toLowerCase().includes("испания")
            ? []
            : ["14 июля, 10:15", "18 июля, 12:40", "25 июля, 09:30"],
        bookAppointmentPlaceholder: () => "Booking API is not connected yet",
        createPaymentPlaceholder: () => "Payment provider is not connected yet"
      }
    };
  }, [state]);

  return <DemoStoreContext.Provider value={value}>{children}</DemoStoreContext.Provider>;
}

export const useDemoStore = () => {
  const context = useContext(DemoStoreContext);
  if (!context) {
    throw new Error("useDemoStore must be used inside DemoStoreProvider");
  }

  return context;
};
