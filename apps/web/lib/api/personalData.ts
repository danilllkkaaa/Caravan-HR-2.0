import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from './client';
import type {
  BankAccount,
  ChangeRequest,
  ChangeRequestSection,
  CitizenshipRecord,
  EducationRecord,
  EmergencyContact,
  EmployeeAddress,
  EmployeeContact,
  FamilyMember,
  FullProfileResponse,
  IdentityDocument,
  MedicalCertificate,
  PersonalData,
  SocialInfo,
} from '@corp-portal/shared-types';

type Source = '1c' | 'user' | 'hr_approved';

interface BackendEnvelope<T> {
  items?: T[];
  total?: number;
}

const source = (value?: string): Source => (value as Source | undefined) ?? 'user';

function mapPersonalData(row: any | null): PersonalData | null {
  if (!row) return null;
  return {
    id: row.id,
    employeeId: row.employee_id,
    firstNameEn: row.first_name_en ?? null,
    lastNameEn: row.last_name_en ?? null,
    middleNameEn: row.middle_name_en ?? null,
    gender: row.gender ?? null,
    nationality: row.nationality ?? null,
    placeOfBirth: row.place_of_birth ?? null,
    maritalStatus: row.marital_status ?? null,
    source: source(row.data_source),
    lastSyncedAt: row['1c_last_synced_at'] ?? null,
  };
}

function personalDataBody(data: Partial<PersonalData>) {
  return {
    first_name_en: data.firstNameEn,
    last_name_en: data.lastNameEn,
    middle_name_en: data.middleNameEn,
    gender: data.gender,
    nationality: data.nationality,
    place_of_birth: data.placeOfBirth,
    marital_status: data.maritalStatus,
  };
}

function mapDocument(row: any): IdentityDocument {
  return {
    id: row.id,
    documentType: row.document_type,
    series: row.series ?? null,
    number: row.number,
    issuedBy: row.issued_by,
    issueDate: row.issue_date,
    expiryDate: row.expiry_date ?? null,
    documentUrl: row.document_url ?? null,
    isActive: row.is_active,
    source: source(row.data_source),
  };
}

function documentBody(data: Partial<IdentityDocument>) {
  return {
    document_type: data.documentType,
    series: data.series,
    number: data.number,
    issued_by: data.issuedBy,
    issue_date: data.issueDate,
    expiry_date: data.expiryDate,
    document_url: data.documentUrl,
  };
}

function mapAddress(row: any): EmployeeAddress {
  return {
    id: row.id,
    addressType: row.address_type,
    country: row.country,
    region: row.region ?? null,
    city: row.city,
    street: row.street ?? null,
    house: row.house ?? null,
    apartment: row.apartment ?? null,
    source: source(row.data_source),
  };
}

function addressBody(data: Partial<EmployeeAddress>) {
  return {
    country: data.country,
    region: data.region,
    city: data.city,
    street: data.street,
    house: data.house,
    apartment: data.apartment,
  };
}

function mapCitizenship(row: any): CitizenshipRecord {
  return {
    id: row.id,
    citizenship: row.citizenship_country,
    status: row.status,
    iinInCountry: row.iin_in_country ?? null,
    isPrimary: row.is_primary,
    source: source(row.data_source),
  };
}

function mapEducation(row: any): EducationRecord {
  return {
    id: row.id,
    educationType: row.education_type,
    institutionName: row.institution_name,
    specialty: row.specialty ?? null,
    qualification: row.qualification ?? null,
    graduationDate: row.graduation_date ?? null,
    documentNumber: row.document_number ?? null,
    documentUrl: row.document_url ?? null,
    source: source(row.data_source),
  };
}

function educationBody(data: Partial<EducationRecord>) {
  return {
    education_type: data.educationType,
    institution_name: data.institutionName,
    specialty: data.specialty,
    qualification: data.qualification,
    graduation_date: data.graduationDate,
    document_number: data.documentNumber,
    document_url: data.documentUrl,
  };
}

function mapFamily(row: any): FamilyMember {
  return {
    id: row.id,
    memberType: row.member_type,
    firstName: row.first_name,
    lastName: row.last_name,
    middleName: row.middle_name ?? null,
    birthDate: row.birth_date ?? null,
    iin: row.iin_masked ?? null,
    birthCertNumber: row.birth_cert_number ?? null,
    birthCertSeries: row.birth_cert_series ?? null,
    birthCertIssueDate: row.birth_cert_issue_date ?? null,
    birthCertIssuedBy: row.birth_cert_issued_by ?? null,
    spouseStatus: row.spouse_status ?? null,
    marriageCertNumber: row.marriage_cert_number ?? null,
    marriageCertIssueDate: row.marriage_cert_issue_date ?? null,
    marriageCertOrg: row.marriage_cert_org ?? null,
    documentUrl: row.document_url ?? null,
    source: source(row.data_source),
  };
}

function familyBody(data: Partial<FamilyMember>) {
  return {
    member_type: data.memberType,
    first_name: data.firstName,
    last_name: data.lastName,
    middle_name: data.middleName,
    birth_date: data.birthDate,
    iin: data.iin,
    birth_cert_number: data.birthCertNumber,
    birth_cert_series: data.birthCertSeries,
    birth_cert_issue_date: data.birthCertIssueDate,
    birth_cert_issued_by: data.birthCertIssuedBy,
    spouse_status: data.spouseStatus,
    marriage_cert_number: data.marriageCertNumber,
    marriage_cert_issue_date: data.marriageCertIssueDate,
    marriage_cert_org: data.marriageCertOrg,
    document_url: data.documentUrl,
  };
}

function mapEmergency(row: any | null): EmergencyContact | null {
  if (!row) return null;
  return {
    id: row.id,
    fullName: row.full_name,
    phone: row.phone,
    address: row.address ?? null,
    relationship: row.relationship,
  };
}

function emergencyBody(data: Partial<EmergencyContact>) {
  return {
    full_name: data.fullName,
    phone: data.phone,
    address: data.address,
    relationship: data.relationship,
  };
}

function mapContacts(row: any | null): EmployeeContact | null {
  if (!row) return null;
  return {
    id: row.id,
    employeeId: row.employee_id,
    email: row.email ?? '',
    mobilePhone: row.mobile_phone ?? '',
    homePhone: row.home_phone ?? null,
    additionalPhone: row.additional_phone ?? null,
    source: source(row.data_source),
  };
}

function contactsBody(data: Partial<EmployeeContact>) {
  return {
    email: data.email,
    mobile_phone: data.mobilePhone,
    home_phone: data.homePhone,
    additional_phone: data.additionalPhone,
  };
}

function mapSocial(row: any | null): SocialInfo | null {
  if (!row) return null;
  return {
    id: row.id,
    pensionStatus: row.pension_status ?? null,
    hasDisability: row.has_disability,
    disabilityGroup: row.disability_group ?? null,
    isWw2Veteran: row.is_ww2_veteran,
    isWw2Family: row.is_ww2_family,
    documentUrl: row.document_url ?? null,
    source: source(row.data_source),
  };
}

function socialBody(data: Partial<SocialInfo>) {
  return {
    pension_status: data.pensionStatus,
    has_disability: data.hasDisability,
    disability_group: data.disabilityGroup,
    is_ww2_veteran: data.isWw2Veteran,
    is_ww2_family: data.isWw2Family,
    document_url: data.documentUrl,
  };
}

function mapMedical(row: any): MedicalCertificate {
  return {
    id: row.id,
    certType: row.cert_type,
    certNumber: row.cert_number,
    issueDate: row.issue_date,
    expiryDate: row.expiry_date ?? null,
    documentUrl: row.document_url,
    createdAt: row.created_at,
  };
}

function medicalBody(data: Partial<MedicalCertificate>) {
  return {
    cert_type: data.certType,
    cert_number: data.certNumber,
    issue_date: data.issueDate,
    expiry_date: data.expiryDate,
    document_url: data.documentUrl,
  };
}

function mapBank(row: any): BankAccount {
  return {
    id: row.id,
    bankName: row.bank_name,
    accountNumber: row.account_number_masked ?? '',
    bik: row.bik,
    accountType: row.account_type,
    holderName: row.holder_name,
    documentUrl: row.document_url ?? null,
    isPrimary: row.is_primary,
    source: source(row.data_source),
  };
}

function bankBody(data: Partial<BankAccount>) {
  return {
    bank_name: data.bankName,
    account_number: data.accountNumber,
    bik: data.bik,
    account_type: data.accountType,
    holder_name: data.holderName,
    document_url: data.documentUrl,
    is_primary: data.isPrimary,
  };
}

function mapChangeRequest(row: any): ChangeRequest {
  return {
    id: row.id,
    employeeId: row.employee_id,
    section: row.section,
    fieldName: row.field_name,
    oldValue: row.old_value ?? {},
    newValue: row.new_value ?? {},
    comment: row.comment ?? null,
    documentUrl: row.document_url ?? null,
    hrEmail: row.hr_email,
    status: row.status,
    hrComment: row.hr_comment ?? null,
    processedAt: row.processed_at ?? null,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

// ===== Full profile =====

export async function getFullProfile(): Promise<FullProfileResponse> {
  const raw = await apiGet<any>('/profile/full');
  return {
    personalData: mapPersonalData(raw.personal_data),
    citizenship: (raw.citizenship ?? []).map(mapCitizenship),
    documents: (raw.documents ?? []).map(mapDocument),
    contacts: mapContacts(raw.contacts),
    addresses: (raw.addresses ?? []).map(mapAddress),
    education: (raw.education ?? []).map(mapEducation),
    family: (raw.family ?? []).map(mapFamily),
    emergencyContact: mapEmergency(raw.emergency_contacts?.[0] ?? null),
    socialInfo: mapSocial(raw.social_info),
    medicalCerts: (raw.medical_certificates ?? []).map(mapMedical),
    bankAccounts: (raw.bank_accounts ?? []).map(mapBank),
    pendingChangeRequests: 0,
  };
}

// ===== Personal Data =====

export async function getPersonalData(): Promise<PersonalData> {
  const raw = await apiGet<{ personal_data: any }>('/profile/personal-data');
  return mapPersonalData(raw.personal_data) as PersonalData;
}

export async function updatePersonalData(
  data: Partial<Omit<PersonalData, 'id' | 'employeeId' | 'source' | 'lastSyncedAt'>>
): Promise<PersonalData> {
  const raw = await apiPatch<{ personal_data: any }>('/profile/personal-data?is_first_fill=true', personalDataBody(data));
  return mapPersonalData(raw.personal_data) as PersonalData;
}

// ===== Contacts =====

export async function getContacts(): Promise<EmployeeContact | null> {
  const raw = await apiGet<{ contacts: any }>('/profile/contacts');
  return mapContacts(raw.contacts);
}

export async function updateContacts(
  data: Partial<Omit<EmployeeContact, 'id' | 'employeeId' | 'source'>>
): Promise<EmployeeContact> {
  const raw = await apiPut<{ contacts: any }>('/profile/contacts', contactsBody(data));
  return mapContacts(raw.contacts) as EmployeeContact;
}

// ===== Documents =====

export async function getDocuments(): Promise<IdentityDocument[]> {
  const raw = await apiGet<{ documents: any[] }>('/profile/documents');
  return raw.documents.map(mapDocument);
}

export async function addDocument(
  data: Omit<IdentityDocument, 'id' | 'source'>
): Promise<IdentityDocument> {
  const raw = await apiPost<{ document: any }>('/profile/documents', documentBody(data));
  return mapDocument(raw.document);
}

export async function getDocumentDownloadUrl(id: string): Promise<{ url: string }> {
  const raw = await apiGet<{ download_url: string }>(`/profile/documents/${id}/download-url`);
  return { url: raw.download_url };
}

export async function getDocumentUploadUrl(_filename: string): Promise<{ uploadUrl: string; fileKey: string }> {
  const raw = await apiPost<{ upload_url: string; object_key: string }>('/profile/documents/upload-url');
  return { uploadUrl: raw.upload_url, fileKey: raw.object_key };
}

// ===== Addresses =====

export async function getAddresses(): Promise<EmployeeAddress[]> {
  const raw = await apiGet<{ addresses: any[] }>('/profile/addresses');
  return raw.addresses.map(mapAddress);
}

export async function updateAddress(
  type: 'registration' | 'residence',
  data: Partial<Omit<EmployeeAddress, 'id' | 'addressType' | 'source'>>
): Promise<EmployeeAddress> {
  const raw = await apiPatch<{ address: any }>(`/profile/addresses/${type}?is_first_fill=true`, addressBody(data));
  return mapAddress(raw.address);
}

// ===== Education =====

export async function getEducation(): Promise<EducationRecord[]> {
  const raw = await apiGet<{ education: any[] }>('/profile/education');
  return raw.education.map(mapEducation);
}

export async function addEducation(
  data: Omit<EducationRecord, 'id' | 'source'>
): Promise<EducationRecord> {
  const raw = await apiPost<{ record: any }>('/profile/education', educationBody(data));
  return mapEducation(raw.record);
}

export async function updateEducation(
  id: string,
  data: Partial<Omit<EducationRecord, 'id' | 'source'>>
): Promise<EducationRecord> {
  const raw = await apiPut<{ record: any }>(`/profile/education/${id}`, educationBody(data));
  return mapEducation(raw.record);
}

export function deleteEducation(id: string): Promise<void> {
  return apiDelete<void>(`/profile/education/${id}`);
}

// ===== Family =====

export async function getFamily(): Promise<FamilyMember[]> {
  const raw = await apiGet<{ family: any[] }>('/profile/family');
  return raw.family.map(mapFamily);
}

export async function addFamilyMember(
  data: Omit<FamilyMember, 'id' | 'source'>
): Promise<FamilyMember> {
  const raw = await apiPost<{ member: any }>('/profile/family', familyBody(data));
  return mapFamily(raw.member);
}

export async function updateFamilyMember(
  id: string,
  data: Partial<Omit<FamilyMember, 'id' | 'source'>>
): Promise<FamilyMember> {
  const raw = await apiPut<{ member: any }>(`/profile/family/${id}`, familyBody(data));
  return mapFamily(raw.member);
}

export function deleteFamilyMember(id: string): Promise<void> {
  return apiDelete<void>(`/profile/family/${id}`);
}

// ===== Emergency Contact =====

export async function getEmergencyContact(): Promise<EmergencyContact | null> {
  const raw = await apiGet<{ emergency_contact: any }>('/profile/emergency-contact');
  return mapEmergency(raw.emergency_contact);
}

export async function updateEmergencyContact(
  data: Omit<EmergencyContact, 'id'>
): Promise<EmergencyContact> {
  const raw = await apiPut<{ emergency_contact: any }>('/profile/emergency-contact', emergencyBody(data));
  return mapEmergency(raw.emergency_contact) as EmergencyContact;
}

// ===== Social Info =====

export async function getSocialInfo(): Promise<SocialInfo | null> {
  const raw = await apiGet<{ social_info: any }>('/profile/social-info');
  return mapSocial(raw.social_info);
}

export async function updateSocialInfo(
  data: Partial<Omit<SocialInfo, 'id' | 'source'>>
): Promise<SocialInfo> {
  const raw = await apiPatch<{ social_info: any }>('/profile/social-info', socialBody(data));
  return mapSocial(raw.social_info) as SocialInfo;
}

// ===== Medical Certificates =====

export async function getMedicalCerts(): Promise<MedicalCertificate[]> {
  const raw = await apiGet<{ medical_certificates: any[] }>('/profile/medical-certs');
  return raw.medical_certificates.map(mapMedical);
}

export async function addMedicalCert(
  data: Omit<MedicalCertificate, 'id' | 'createdAt'>
): Promise<MedicalCertificate> {
  const raw = await apiPost<{ certificate: any }>('/profile/medical-certs', medicalBody(data));
  return mapMedical(raw.certificate);
}

export function deleteMedicalCert(id: string): Promise<void> {
  return apiDelete<void>(`/profile/medical-certs/${id}`);
}

export async function getMedicalCertUploadUrl(_filename: string): Promise<{ uploadUrl: string; fileKey: string }> {
  const raw = await apiPost<{ upload_url: string; object_key: string }>('/profile/medical-certs/upload-url');
  return { uploadUrl: raw.upload_url, fileKey: raw.object_key };
}

// ===== Bank Accounts =====

export async function getBankAccounts(): Promise<BankAccount[]> {
  const raw = await apiGet<{ bank_accounts: any[] }>('/profile/bank-accounts');
  return raw.bank_accounts.map(mapBank);
}

export async function addBankAccount(
  data: Omit<BankAccount, 'id' | 'source'>
): Promise<BankAccount> {
  const raw = await apiPost<{ bank_account: any }>('/profile/bank-accounts', bankBody(data));
  return mapBank(raw.bank_account);
}

export function deleteBankAccount(id: string): Promise<void> {
  return apiDelete<void>(`/profile/bank-accounts/${id}`);
}

export async function getBankUploadUrl(_filename: string): Promise<{ uploadUrl: string; fileKey: string }> {
  const raw = await apiPost<{ upload_url: string; object_key: string }>('/profile/bank-accounts/upload-url');
  return { uploadUrl: raw.upload_url, fileKey: raw.object_key };
}

// ===== Change Requests =====

export async function getChangeRequests(): Promise<ChangeRequest[]> {
  const raw = await apiGet<BackendEnvelope<any>>('/profile/change-requests');
  return (raw.items ?? []).map(mapChangeRequest);
}

export interface CreateChangeRequestPayload {
  section: ChangeRequestSection;
  fieldName: string;
  oldValue: Record<string, unknown>;
  newValue: Record<string, unknown>;
  comment?: string;
  documentUrl?: string;
}

export async function createChangeRequest(data: CreateChangeRequestPayload): Promise<ChangeRequest> {
  const raw = await apiPost<{ change_request: any }>('/profile/change-requests', {
    section: data.section,
    field_name: data.fieldName,
    old_value: data.oldValue,
    new_value: data.newValue,
    comment: data.comment,
    document_url: data.documentUrl,
  });
  return mapChangeRequest(raw.change_request);
}

export async function cancelChangeRequest(id: string): Promise<ChangeRequest> {
  await apiDelete<void>(`/profile/change-requests/${id}`);
  return getChangeRequests().then((items) => items.find((item) => item.id === id) as ChangeRequest);
}
