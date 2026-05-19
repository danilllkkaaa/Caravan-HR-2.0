// ============================================================
// Enums
// ============================================================

export enum Role {
  Employee = 'employee',
  Manager = 'manager',
  HR = 'hr',
  Admin = 'admin',
}

export enum VacationRequestStatus {
  Draft = 'draft',
  Pending = 'pending',
  ApprovedByManager = 'approved_by_manager',
  ApprovedByHR = 'approved_by_hr',
  Rejected = 'rejected',
  Cancelled = 'cancelled',
}

export enum SickLeaveStatus {
  Open = 'open',
  Closed = 'closed',
  Confirmed = 'confirmed',
  Rejected = 'rejected',
}

export enum TimesheetStatus {
  Present = 'present',
  Absent = 'absent',
  Holiday = 'holiday',
  Weekend = 'weekend',
  OnVacation = 'on_vacation',
  SickLeave = 'sick_leave',
  BusinessTrip = 'business_trip',
  Remote = 'remote',
  HalfDay = 'half_day',
}

export enum NotificationType {
  VacationApproved = 'vacation_approved',
  VacationRejected = 'vacation_rejected',
  VacationPending = 'vacation_pending',
  SickLeaveOpened = 'sick_leave_opened',
  SickLeaveClosed = 'sick_leave_closed',
  TimesheetReminder = 'timesheet_reminder',
  PasswordChanged = 'password_changed',
  SystemAnnouncement = 'system_announcement',
  BalanceUpdated = 'balance_updated',
  ApprovalRequired = 'approval_required',
}

export enum WorkLocationType {
  Office = 'office',
  Remote = 'remote',
  Hybrid = 'hybrid',
}

// ============================================================
// Core Domain Entities
// ============================================================

export interface Department {
  id: number;
  name: string;
  code: string;
  parentId: number | null;
  managerId: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface Position {
  id: number;
  title: string;
  code: string;
  departmentId: number;
  gradeLevel: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface WorkLocation {
  id: number;
  name: string;
  address: string;
  type: WorkLocationType;
  timezone: string;
}

export interface User {
  id: number;
  email: string;
  role: Role;
  isActive: boolean;
  isSuperuser: boolean;
  createdAt: string;
  updatedAt: string;
  lastLoginAt: string | null;
}

export interface Employee {
  id: number;
  userId: number;
  user: User;
  firstName: string;
  lastName: string;
  middleName: string | null;
  fullName: string;
  phone: string | null;
  avatarUrl: string | null;
  hireDate: string;
  dismissDate: string | null;
  departmentId: number;
  department: Department;
  positionId: number;
  position: Position;
  managerId: number | null;
  manager: Employee | null;
  workLocationId: number | null;
  workLocation: WorkLocation | null;
  employeeNumber: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// ============================================================
// Vacation Domain
// ============================================================

export interface VacationType {
  id: number;
  name: string;
  code: string;
  isPaid: boolean;
  requiresDocument: boolean;
  maxDaysPerYear: number | null;
  description: string | null;
}

export interface VacationBalance {
  id: number;
  employeeId: number;
  vacationTypeId: number;
  vacationType: VacationType;
  year: number;
  totalDays: number;
  usedDays: number;
  pendingDays: number;
  remainingDays: number;
  carriedOverDays: number;
  updatedAt: string;
}

export interface VacationRequest {
  id: number;
  employeeId: number;
  employee: Employee;
  vacationTypeId: number;
  vacationType: VacationType;
  startDate: string;
  endDate: string;
  workingDays: number;
  calendarDays: number;
  status: VacationRequestStatus;
  comment: string | null;
  rejectionReason: string | null;
  managerId: number | null;
  manager: Employee | null;
  hrId: number | null;
  managerApprovedAt: string | null;
  hrApprovedAt: string | null;
  rejectedAt: string | null;
  cancelledAt: string | null;
  createdAt: string;
  updatedAt: string;
}

// ============================================================
// Sick Leave Domain
// ============================================================

export interface SickLeave {
  id: string;
  employeeId: string;
  employee?: Employee;
  startDate: string;
  endDate: string | null;
  calendarDays: number | null;
  workingDays: number | null;
  status: SickLeaveStatus;
  diagnosisCode: string | null;
  documentNumber: string | null;
  documentUrl: string | null;
  comment: string | null;
  closedById: string | null;
  closedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

// ============================================================
// Timesheet Domain
// ============================================================

export interface TimesheetEntry {
  id: number;
  employeeId: number;
  date: string;
  status: TimesheetStatus;
  checkIn: string | null;
  checkOut: string | null;
  hoursWorked: number | null;
  overtimeHours: number | null;
  locationId: number | null;
  location: WorkLocation | null;
  note: string | null;
  isManualEntry: boolean;
  approvedById: number | null;
  approvedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TimesheetMonth {
  year: number;
  month: number;
  entries: TimesheetEntry[];
  summary: {
    totalWorkingDays: number;
    presentDays: number;
    absentDays: number;
    vacationDays: number;
    sickLeaveDays: number;
    holidayDays: number;
    totalHoursWorked: number;
    totalOvertimeHours: number;
    attendanceRate: number;
  };
}

// ============================================================
// Notifications
// ============================================================

export interface Notification {
  id: number;
  userId: number;
  type: NotificationType;
  title: string;
  body: string;
  isRead: boolean;
  readAt: string | null;
  entityType: string | null;
  entityId: number | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

// ============================================================
// Auth / Security
// ============================================================

export interface RefreshToken {
  id: number;
  userId: number;
  tokenHash: string;
  deviceInfo: string | null;
  ipAddress: string | null;
  expiresAt: string;
  revokedAt: string | null;
  createdAt: string;
}

export interface UserSession {
  id: number;
  deviceInfo: string | null;
  ipAddress: string | null;
  createdAt: string;
  lastUsedAt: string;
  isCurrent: boolean;
}

export interface AuditLog {
  id: number;
  userId: number | null;
  action: string;
  entityType: string | null;
  entityId: number | null;
  oldValues: Record<string, unknown> | null;
  newValues: Record<string, unknown> | null;
  ipAddress: string | null;
  userAgent: string | null;
  createdAt: string;
}

// ============================================================
// Aggregates
// ============================================================

export interface DashboardData {
  employee: Employee;
  vacationBalances: VacationBalance[];
  todayAttendance: TimesheetEntry | null;
  pendingRequests: {
    vacations: number;
    sickLeaves: number;
  };
  recentNotifications: Notification[];
  upcomingVacations: VacationRequest[];
  teamOnLeave: Employee[];
}

// ============================================================
// API Response Wrappers
// ============================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface CursorPaginatedResponse<T> {
  items: T[];
  nextCursor: string | null;
  prevCursor: string | null;
  hasMore: boolean;
  total: number;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, string[]> | string | null;
}

export interface ApiError {
  error: ApiErrorDetail;
}

// ============================================================
// Request / Input types
// ============================================================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  user: User;
  employee: Employee;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface CreateVacationRequest {
  vacationTypeId: number;
  startDate: string;
  endDate: string;
  comment?: string;
}

export interface CreateSickLeaveRequest {
  startDate: string;
  comment?: string;
}

export interface CloseSickLeaveRequest {
  endDate: string;
  documentNumber?: string;
  diagnosisCode?: string;
  comment?: string;
}

export interface ApproveRejectRequest {
  comment?: string;
}

export interface RejectRequest {
  reason: string;
}

// ===== Personal Data Module =====

export type DataSource = '1c' | 'user' | 'hr_approved';

export interface DataSourceMeta {
  source: DataSource;
  isEditable: boolean; // true если source='user' или поле пустое
  lastSyncedAt?: string | null;
}

export enum ChangeRequestStatus {
  Sent = 'sent',
  UnderReview = 'under_review',
  Approved = 'approved',
  Rejected = 'rejected',
}

export enum ChangeRequestSection {
  BasicData = 'basic_data',
  Citizenship = 'citizenship',
  Document = 'document',
  Address = 'address',
  Contacts = 'contacts',
  Education = 'education',
  Family = 'family',
  EmergencyContact = 'emergency_contact',
  SocialInfo = 'social_info',
  Medical = 'medical',
  Bank = 'bank',
}

export interface PersonalData {
  id: string;
  employeeId: string;
  firstNameEn: string | null;
  lastNameEn: string | null;
  middleNameEn: string | null;
  gender: 'male' | 'female' | null;
  nationality: string | null;
  placeOfBirth: string | null;
  maritalStatus: 'single' | 'married' | 'divorced' | 'widowed' | null;
  source: DataSource;
  lastSyncedAt: string | null;
}

export interface CitizenshipRecord {
  id: string;
  citizenship: string;
  status: 'rk_citizen' | 'foreign_citizen' | 'stateless';
  iinInCountry: string | null;
  isPrimary: boolean;
  source: DataSource;
}

export interface IdentityDocument {
  id: string;
  documentType: 'national_id' | 'passport' | 'residence_permit' | 'other';
  series: string | null;
  number: string;
  issuedBy: string;
  issueDate: string;
  expiryDate: string | null;
  documentUrl: string | null;
  isActive: boolean;
  source: DataSource;
}

export interface EmployeeAddress {
  id: string;
  addressType: 'registration' | 'residence';
  country: string;
  region: string | null;
  city: string;
  street: string | null;
  house: string | null;
  apartment: string | null;
  source: DataSource;
}

export interface EducationRecord {
  id: string;
  educationType: 'higher' | 'secondary' | 'technical' | 'advanced_qualification' | 'other';
  institutionName: string;
  specialty: string | null;
  qualification: string | null;
  graduationDate: string | null;
  documentNumber: string | null;
  documentUrl: string | null;
  source: DataSource;
}

export interface FamilyMember {
  id: string;
  memberType: 'child' | 'spouse' | 'ex_spouse';
  firstName: string;
  lastName: string;
  middleName: string | null;
  birthDate: string | null;
  iin: string | null;
  // children
  birthCertNumber: string | null;
  birthCertSeries: string | null;
  birthCertIssueDate: string | null;
  birthCertIssuedBy: string | null;
  // spouse
  spouseStatus: string | null;
  marriageCertNumber: string | null;
  marriageCertIssueDate: string | null;
  marriageCertOrg: string | null;
  documentUrl: string | null;
  source: DataSource;
}

export interface EmergencyContact {
  id: string;
  fullName: string;
  phone: string;
  address: string | null;
  relationship: string;
}

export interface EmployeeContact {
  id: string;
  employeeId: string;
  email: string;
  mobilePhone: string;
  homePhone: string | null;
  additionalPhone: string | null;
  source: DataSource;
}

export interface SocialInfo {
  id: string;
  pensionStatus: string | null;
  hasDisability: boolean;
  disabilityGroup: number | null;
  isWw2Veteran: boolean;
  isWw2Family: boolean;
  documentUrl: string | null;
  source: DataSource;
}

export interface MedicalCertificate {
  id: string;
  certType: 'narco_dispensary' | 'psycho_dispensary' | 'form_075';
  certNumber: string;
  issueDate: string;
  expiryDate: string | null;
  documentUrl: string;
  createdAt: string;
}

export interface BankAccount {
  id: string;
  bankName: string;
  accountNumber: string; // masked: ****1234
  bik: string;
  accountType: 'standard' | 'social' | 'other';
  holderName: string;
  documentUrl: string | null;
  isPrimary: boolean;
  source: DataSource;
}

export interface ChangeRequest {
  id: string;
  employeeId: string;
  section: ChangeRequestSection;
  fieldName: string;
  oldValue: Record<string, unknown>;
  newValue: Record<string, unknown>;
  comment: string | null;
  documentUrl: string | null;
  hrEmail: string;
  status: ChangeRequestStatus;
  hrComment: string | null;
  processedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface FullProfileResponse {
  personalData: PersonalData | null;
  citizenship: CitizenshipRecord[];
  documents: IdentityDocument[];
  contacts: EmployeeContact | null;
  addresses: EmployeeAddress[];
  education: EducationRecord[];
  family: FamilyMember[];
  emergencyContact: EmergencyContact | null;
  socialInfo: SocialInfo | null;
  medicalCerts: MedicalCertificate[];
  bankAccounts: BankAccount[];
  pendingChangeRequests: number;
}
