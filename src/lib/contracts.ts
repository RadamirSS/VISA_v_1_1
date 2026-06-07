import { ApplicationRecord, DocumentItem, Lead, LeadFormValues, LeadStatus, VisaFormData } from "@/lib/types";

export type LeadServiceContract = {
  createLead: (payload: LeadFormValues) => Promise<Lead>;
  getLead: (id: string) => Promise<Lead | undefined>;
  listLeads: () => Promise<Lead[]>;
  updateLeadStatus: (id: string, status: LeadStatus) => Promise<void>;
};

export type PortalServiceContract = {
  registerWithInvite: (inviteToken: string, payload: { password: string }) => Promise<{ ok: boolean; message: string }>;
  loginMock: (payload: { email: string; password: string }) => Promise<{ ok: boolean; message: string }>;
  getClientApplication: () => Promise<ApplicationRecord | null>;
  updateClientProfile: (payload: ApplicationRecord["profile"]) => Promise<void>;
  updateVisaForm: (payload: Partial<VisaFormData>) => Promise<void>;
  getApplicationStatus: () => Promise<string[]>;
};

export type DocumentsServiceContract = {
  listRequiredDocuments: (applicationId: string) => Promise<DocumentItem[]>;
  uploadDocumentMock: (
    applicationId: string,
    documentType: string,
    metadata: { fileName: string; fileType: string; fileSizeKb: number; clientComment: string }
  ) => Promise<void>;
  updateDocumentStatus: (documentId: string, status: DocumentItem["status"]) => Promise<void>;
  addDocumentComment: (documentId: string, comment: string) => Promise<void>;
};

export type AppointmentServiceContract = {
  searchAppointmentSlots: (payload: { query: string }) => Promise<string[]>;
  bookAppointmentPlaceholder: (payload: { applicationId: string; slot: string }) => Promise<{ ok: false; message: string }>;
};

export type PaymentServiceContract = {
  createPaymentPlaceholder: (payload: { applicationId: string; amount: number }) => Promise<{ ok: false; message: string }>;
};
