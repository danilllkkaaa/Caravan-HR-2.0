import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '@/lib/api/personalData';
import type {
  PersonalData,
  EducationRecord,
  FamilyMember,
  EmergencyContact,
  EmployeeContact,
  SocialInfo,
  IdentityDocument,
  EmployeeAddress,
  MedicalCertificate,
  BankAccount,
} from '@corp-portal/shared-types';
import type { CreateChangeRequestPayload } from '@/lib/api/personalData';

// ===== Query keys =====
export const personalDataKeys = {
  all: ['personal-data'] as const,
  fullProfile: () => [...personalDataKeys.all, 'full-profile'] as const,
  basic: () => [...personalDataKeys.all, 'basic'] as const,
  documents: () => [...personalDataKeys.all, 'documents'] as const,
  contacts: () => [...personalDataKeys.all, 'contacts'] as const,
  addresses: () => [...personalDataKeys.all, 'addresses'] as const,
  education: () => [...personalDataKeys.all, 'education'] as const,
  family: () => [...personalDataKeys.all, 'family'] as const,
  emergencyContact: () => [...personalDataKeys.all, 'emergency-contact'] as const,
  socialInfo: () => [...personalDataKeys.all, 'social-info'] as const,
  medicalCerts: () => [...personalDataKeys.all, 'medical-certs'] as const,
  bankAccounts: () => [...personalDataKeys.all, 'bank-accounts'] as const,
  changeRequests: () => [...personalDataKeys.all, 'change-requests'] as const,
};

// ===== Queries =====

export function useFullProfile() {
  return useQuery({
    queryKey: personalDataKeys.fullProfile(),
    queryFn: api.getFullProfile,
    staleTime: 5 * 60 * 1000,
  });
}

export function usePersonalData() {
  return useQuery({
    queryKey: personalDataKeys.basic(),
    queryFn: api.getPersonalData,
    staleTime: 5 * 60 * 1000,
  });
}

export function useDocuments() {
  return useQuery({
    queryKey: personalDataKeys.documents(),
    queryFn: api.getDocuments,
    staleTime: 30 * 60 * 1000,
  });
}

export function useContacts() {
  return useQuery({
    queryKey: personalDataKeys.contacts(),
    queryFn: api.getContacts,
    staleTime: 30 * 60 * 1000,
  });
}

export function useAddresses() {
  return useQuery({
    queryKey: personalDataKeys.addresses(),
    queryFn: api.getAddresses,
    staleTime: 30 * 60 * 1000,
  });
}

export function useEducation() {
  return useQuery({
    queryKey: personalDataKeys.education(),
    queryFn: api.getEducation,
    staleTime: 30 * 60 * 1000,
  });
}

export function useFamily() {
  return useQuery({
    queryKey: personalDataKeys.family(),
    queryFn: api.getFamily,
    staleTime: 30 * 60 * 1000,
  });
}

export function useEmergencyContact() {
  return useQuery({
    queryKey: personalDataKeys.emergencyContact(),
    queryFn: api.getEmergencyContact,
    staleTime: 30 * 60 * 1000,
  });
}

export function useSocialInfo() {
  return useQuery({
    queryKey: personalDataKeys.socialInfo(),
    queryFn: api.getSocialInfo,
    staleTime: 30 * 60 * 1000,
  });
}

export function useMedicalCerts() {
  return useQuery({
    queryKey: personalDataKeys.medicalCerts(),
    queryFn: api.getMedicalCerts,
    staleTime: 30 * 60 * 1000,
  });
}

export function useBankAccounts() {
  return useQuery({
    queryKey: personalDataKeys.bankAccounts(),
    queryFn: api.getBankAccounts,
    staleTime: 30 * 60 * 1000,
  });
}

export function useChangeRequests() {
  return useQuery({
    queryKey: personalDataKeys.changeRequests(),
    queryFn: api.getChangeRequests,
    staleTime: 2 * 60 * 1000,
    refetchInterval: 2 * 60 * 1000,
  });
}

// ===== Mutations =====

export function useUpdatePersonalData() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Omit<PersonalData, 'id' | 'employeeId' | 'source' | 'lastSyncedAt'>>) =>
      api.updatePersonalData(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.basic() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useAddDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<IdentityDocument, 'id' | 'source'>) => api.addDocument(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.documents() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useUpdateContacts() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Omit<EmployeeContact, 'id' | 'employeeId' | 'source'>>) =>
      api.updateContacts(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.contacts() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useUpdateAddress() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      type,
      data,
    }: {
      type: 'registration' | 'residence';
      data: Partial<Omit<EmployeeAddress, 'id' | 'addressType' | 'source'>>;
    }) => api.updateAddress(type, data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.addresses() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useAddEducation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<EducationRecord, 'id' | 'source'>) => api.addEducation(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.education() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useUpdateEducation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: Partial<Omit<EducationRecord, 'id' | 'source'>>;
    }) => api.updateEducation(id, data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.education() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useDeleteEducation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteEducation(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.education() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useAddFamilyMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<FamilyMember, 'id' | 'source'>) => api.addFamilyMember(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.family() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useUpdateFamilyMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: Partial<Omit<FamilyMember, 'id' | 'source'>>;
    }) => api.updateFamilyMember(id, data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.family() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useDeleteFamilyMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteFamilyMember(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.family() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useUpdateEmergencyContact() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<EmergencyContact, 'id'>) => api.updateEmergencyContact(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.emergencyContact() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useUpdateSocialInfo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Omit<SocialInfo, 'id' | 'source'>>) => api.updateSocialInfo(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.socialInfo() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useAddMedicalCert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<MedicalCertificate, 'id' | 'createdAt'>) =>
      api.addMedicalCert(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.medicalCerts() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useDeleteMedicalCert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteMedicalCert(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.medicalCerts() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useAddBankAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<BankAccount, 'id' | 'source'>) => api.addBankAccount(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.bankAccounts() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useDeleteBankAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteBankAccount(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.bankAccounts() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useCreateChangeRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateChangeRequestPayload) => api.createChangeRequest(data),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.changeRequests() });
      void qc.invalidateQueries({ queryKey: personalDataKeys.fullProfile() });
    },
  });
}

export function useCancelChangeRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.cancelChangeRequest(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: personalDataKeys.changeRequests() });
    },
  });
}
