export type LeadStatus = "new" | "in_review" | "approved" | "rejected";
export type DocumentStatus = "missing" | "uploaded" | "needs_correction" | "accepted";

export type LeadFormValues = {
  fullName: string;
  phone: string;
  telegram: string;
  email: string;
  citizenship: string;
  location: string;
  schengenCountry: string;
  purpose: string;
  travelDates: string;
  applicantsCount: string;
  previousSchengen: string;
  passportValidity: string;
  comment: string;
  consent: boolean;
};

export type Lead = {
  id: string;
  createdAt: string;
  status: LeadStatus;
  approvalNote?: string;
  inviteToken?: string;
  values: LeadFormValues;
};

export type ClientProfile = {
  password: string;
  phone: string;
  address: string;
  residenceCountry: string;
  residencePermit: string;
  emergencyContact: string;
};

export type VisaFormData = {
  surname: string;
  givenName: string;
  previousNames: string;
  birthDate: string;
  birthPlace: string;
  birthCountry: string;
  nationality: string;
  nationalityAtBirth: string;
  gender: string;
  maritalStatus: string;
  minorDetails: string;
  passportNumber: string;
  passportIssueDate: string;
  passportExpiryDate: string;
  passportAuthority: string;
  passportType: string;
  homeAddress: string;
  email: string;
  phone: string;
  currentResidence: string;
  residencePermitFields: string;
  occupation: string;
  employer: string;
  fundsSource: string;
  mainDestination: string;
  firstEntry: string;
  travelPurpose: string;
  arrivalDate: string;
  departureDate: string;
  entriesRequested: string;
  hostInfo: string;
  itineraryNotes: string;
  previousVisas: string;
  fingerprintsCollected: string;
  previousRefusals: string;
  refusalNotes: string;
  expensesCoveredBy: string;
  accommodationPrepaid: string;
  transportPrepaid: string;
  otherSupport: string;
  dataConsent: boolean;
  accuracyConsent: boolean;
  authorityDisclaimer: boolean;
};

export type DocumentItem = {
  id: string;
  type: string;
  title: string;
  required: boolean;
  guidance: string;
  status: DocumentStatus;
  managerComment: string;
  clientComment: string;
  fileName?: string;
  fileType?: string;
  fileSizeKb?: number;
  uploadedAt?: string;
};

export type ApplicationTimelineStep = {
  key: string;
  title: string;
  description: string;
};

export type ApplicationRecord = {
  id: string;
  leadId: string;
  inviteToken: string;
  registered: boolean;
  managerStatus: LeadStatus;
  fullName: string;
  email: string;
  visaDirection: string;
  profile: ClientProfile;
  visaForm: VisaFormData;
  documents: DocumentItem[];
  timelineCompletedKeys: string[];
};

export type Session = {
  applicationId: string | null;
};

export type DemoState = {
  leads: Lead[];
  applications: ApplicationRecord[];
  session: Session;
};
