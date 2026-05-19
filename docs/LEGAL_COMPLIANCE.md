# Legal and Compliance Requirements
## Corporate HR Portal

**Version:** 1.0  
**Date:** May 2026  
**Scope:** Kazakhstan-oriented HR portal: PWA, mobile app, FastAPI backend, 1C:ZUP sync, Hikvision attendance, MinIO document storage.

> This document is a product and engineering compliance baseline, not a legal opinion. Before production launch, the company lawyer, HR owner, information security owner, and 1C/Hikvision integration owners must validate it against the company's internal policies and current Kazakhstan law.

## 1. Regulatory Assumptions

The portal processes employee HR data, therefore the baseline jurisdiction is the Republic of Kazakhstan unless a separate company policy says otherwise.

Primary sources to verify before launch:

- Law of the Republic of Kazakhstan "On Personal Data and Their Protection": https://adilet.zan.kz/eng/docs/Z1300000094
- Russian text of the same law: https://adilet.zan.kz/rus/docs/Z1300000094
- Rules for collection and processing of personal data: https://adilet.zan.kz/rus/docs/V2000021498
- Health Code, Article 62 on protection of personal medical data: https://adilet.zan.kz/rus/docs/K2000000360
- Rules on personal medical data processing by digital health entities: https://adilet.zan.kz/rus/docs/V2100022550
- Law on Informatization, simple electronic signature: https://adilet.zan.kz/rus/docs/Z1500000418
- Law on Electronic Document and Electronic Digital Signature: https://adilet.zan.kz/rus/docs/Z030000370_

Important known constraints:

- Personal data collection and processing generally requires consent unless a statutory exception applies.
- Consent must be confirmable and should state the operator, data subject, validity period, list of data, third-party transfer, cross-border transfer, and publication in public sources where applicable.
- Storage of personal data should be in a database located in Kazakhstan unless legal counsel approves another model.
- Cross-border transfer requires extra review. If the destination state does not ensure adequate protection, consent or another legal ground is required.
- Medical data and sick leave documents require stricter access controls than ordinary HR profile data.

## 2. Data Controller, Operator, and Processors

Define these roles before implementation:

| Role | Required decision |
|---|---|
| Data owner/controller | Legal entity that owns the employee database and determines processing purposes. |
| Operator | Internal team or vendor operating the portal and processing data on behalf of the owner. |
| Third-party processors | Hosting provider, Sentry, Expo, Apple/Google push services, GitHub, email/SMS provider, object storage provider, 1C vendor, Hikvision integrator. |
| Responsible person | Named employee responsible for personal data processing organization and internal control. |

Required artifacts:

- Personal data processing policy.
- Employee privacy notice.
- Employee consent form, if consent is used as a legal basis.
- Processor agreements or data processing clauses with vendors.
- Internal order appointing the responsible person.
- Internal access matrix approved by HR and security.
- Incident response procedure.
- Data retention and deletion policy.

## 3. Data Inventory and Classification

| Data category | Examples | Sensitivity | Storage decision |
|---|---|---:|---|
| Account data | email, password hash, sessions, device info | High | Postgres in Kazakhstan; password hash only. |
| HR profile | name, personnel number, department, position, manager, hire date, phone | Medium/High | Postgres in Kazakhstan. |
| National identifiers | IIN, identity data if added later | Very high | Avoid in MVP if not required; encrypt field-level; mask in UI/logs. |
| Attendance | entry/exit events, device ID, Hikvision person ID, timesheet | High | Postgres in Kazakhstan; raw payload retention limited. |
| Sick leave | dates, status, uploaded document, comments | Very high | MinIO private bucket in Kazakhstan; strict role access; no diagnosis unless legally required. |
| Payroll | payslip, gross/net, deductions | Very high | Prefer on-demand fetch from 1C; avoid long-term storage in portal. |
| Vacation requests | dates, type, comments, approvals | Medium/High | Postgres in Kazakhstan. |
| Notifications | title, body, payload links | Medium | Do not include sensitive details in push text. |
| Audit logs | actor, action, target, IP, user agent, before/after diff | High | Immutable-style retention; restrict to admin/security. |
| Files | sick leave scans, future material aid documents | Very high | Private object storage; presigned URLs; antivirus scan. |
| Mobile device data | push token, app version, OS, device model | Medium | Store only while session is active or push is enabled. |
| Biometrics | Face ID/Touch ID unlock state | Very high | Do not collect biometric templates. Use only OS-level local authentication. |

Design rule: if a field is not required for a user-facing workflow, 1C sync, reporting, or legal obligation, do not collect it.

## 4. Consent and Privacy Notice

The portal must not rely on a generic checkbox only. Consent and notice must be specific enough for HR processing.

Minimum consent/notice content:

- Legal name, BIN/IIN if applicable, and contacts of the data owner/operator.
- Purposes: HR self-service, vacation management, sick leave processing, attendance/timesheet, notifications, account security, audit, support.
- Data list by category, not vague wording.
- Processing actions: collection, recording, storage, update, use, transfer, blocking, deletion, anonymization.
- Validity period of consent or reference to employment/legal retention period.
- Whether data may be transferred to third parties.
- Whether cross-border transfer may occur.
- Whether any data is published in public sources. Default: no.
- Subject rights: access, correction, blocking, deletion where legally available, withdrawal of consent, complaint procedure.
- Contacts for personal data requests.

Recommended product behavior:

- Show privacy notice at first login.
- Store consent version, timestamp, user ID, IP, user agent, and text hash.
- If legal text changes materially, request re-acceptance.
- Keep consent history, not only the latest boolean.
- Do not block legally required HR processing solely because optional consent is withdrawn; route such cases to HR/legal review.

## 5. Access Control Matrix

Use least privilege by default.

| Resource | Employee | Manager | HR | Admin |
|---|---|---|---|---|
| Own profile | Read, limited edit | Read own | Read own | Read own |
| Other employee profile | No, except directory fields if approved | Direct/indirect subordinates only | Assigned work locations only | All |
| IIN / identity data | Masked or hidden | Hidden | Masked, full only if approved | Masked by default |
| Vacation request | Own create/read/cancel | Approve subordinates | Read by HR scope if needed | All |
| Sick leave status | Own | Status only for subordinates | Full within HR scope | Full |
| Sick leave document | Own | No | Full within HR scope | Full only if operationally required |
| Timesheet | Own | Subordinates summary/detail if approved | HR scope | All |
| Payroll slip | Own only | No | No by default | No by default |
| Audit log | No | No | HR actions only if approved | Full |
| User/session admin | Own sessions | No | No by default | Full |

Implementation requirements:

- Enforce access in backend services, not only in UI.
- Every endpoint must have an explicit authorization rule.
- SQLAdmin must be restricted to a very small admin group and ideally not exposed to the public internet.
- Admin access must be audited.
- Privileged actions should require recent authentication or MFA in a later phase.

## 6. Sick Leave and Medical Data

Sick leave handling is the highest-risk MVP module because it may include medical data.

Product rules:

- Store only data required for HR processing: start date, end date, document key, status, employee, HR processing metadata.
- Do not store diagnosis, treatment details, medical organization notes, or free-form medical details unless legal counsel confirms they are required.
- In the UI, manager should see only operational status: "on sick leave" and dates if approved by HR policy. Manager should not see uploaded scans.
- HR access must be scoped by work location or assigned business unit.
- Uploaded documents must be private and accessible only through short-lived presigned URLs.
- Presigned URL TTL: 5 minutes or less.
- Direct object storage URLs must not be stored in notifications, push payloads, logs, or audit diffs.
- File upload must include MIME/type validation, size limit, malware scan, and content-disposition controls.
- Document preview/download must create an audit event.

Retention:

- Define exact retention with legal/HR. Until confirmed, use conservative access restriction, not automatic deletion.
- Raw uploaded scans should have a documented retention period and deletion workflow.
- If a document was uploaded by mistake, HR/legal must be able to quarantine or delete it with audit trail.

## 7. IIN and Identity Data

IIN and identity data should not be part of MVP unless required by a concrete business process.

If added:

- Store encrypted at application level using AES-GCM or an equivalent authenticated encryption mode.
- Keep encryption keys outside the database.
- Rotate keys with a documented procedure.
- Show masked value by default: `******123456` or similar.
- Never include IIN in logs, Sentry events, analytics, URLs, push notifications, or exported CSV filenames.
- Access full value only through a privileged endpoint with audit logging and purpose selection.

## 8. Attendance, Hikvision, and Workplace Monitoring

Attendance events are personal data and may be perceived as workplace monitoring.

Required policy decisions:

- Employees must be informed that attendance events from access control are used for portal/timesheet purposes.
- Define whether data is used only for attendance visibility or also for disciplinary/payroll decisions.
- Define correction procedure for missed entry/exit events.
- Define who can edit normalized timesheet entries and how corrections are audited.
- Define whether raw Hikvision payloads may include photos or biometric templates. Default requirement: do not store photos/templates in the portal.

Engineering requirements:

- Store only `hikvision_person_id`, event type, device, timestamp, and raw payload fields required for debugging.
- If raw payload contains photos, face templates, or unrelated metadata, strip before persistence.
- Raw payload retention must be short, for example 30-90 days, unless legal/security requires longer.
- Normalized `timesheet_entries` can be retained according to HR/payroll policy.
- Daily reconciliation pull from Hikvision must follow the same minimization rules.
- All manual corrections must be recorded in `audit_log`.

## 9. Payroll and 1C:ZUP

1C is likely the system of record for HR/payroll. The portal should avoid becoming a duplicate payroll archive.

Rules:

- 1C remains the source of truth for employee master data, vacation balances, schedules, payroll slips, and official HR records unless explicitly changed.
- Portal stores sync metadata: external IDs, hashes, last sync time, error state.
- Payslips should be fetched on demand and cached only briefly.
- If payslip caching is needed, cache encrypted and define retention, for example 1 hour or one session.
- Do not show payroll data to managers or admins by default.
- All 1C service credentials must be scoped to only required endpoints.
- 1C API contracts must define data owner, legal basis, and retention per dataset.

## 10. Cross-Border Transfers and Cloud Services

The architecture must assume Kazakhstan data localization for personal data storage.

High-risk services:

- Sentry: may receive exception payloads, breadcrumbs, user IDs, emails, URLs.
- Expo/Apple/Google push: receives push tokens and notification payloads.
- GitHub Actions/GHCR: must not receive production data.
- External object storage outside Kazakhstan.
- Cloudflare tunnels or public debugging tools.
- Support chat/analytics tools if added later.

Requirements:

- Production Postgres, Redis persistence, MinIO, backups, and logs containing personal data should be hosted in Kazakhstan unless legal approves otherwise.
- Disable PII in Sentry. Use user ID only if approved; prefer internal opaque ID.
- Push notifications must contain generic text, for example "New portal notification", not sick leave/payroll details.
- Do not send document URLs, IIN, payroll values, or medical details to third-party cloud services.
- If any processor outside Kazakhstan receives personal data, document the transfer, legal basis, countries, data categories, retention, and safeguards.
- Backups are also personal data storage and must follow the same location and access rules.

## 11. Electronic Approvals and Signatures

Portal actions such as approving vacation or closing a sick leave are not automatically equivalent to an official electronic digital signature.

Classify actions:

| Action | Suggested legal status | Requirement |
|---|---|---|
| Login/password + JWT | Authentication, not official signature | Audit log and session security. |
| Manager approves vacation | Internal workflow approval | Must be backed by internal HR policy/order. |
| Employee submits vacation request | Internal electronic request | Confirm if paper/EDS duplicate is needed. |
| Employee uploads sick leave scan | Submission of supporting document | Confirm whether original/eGov document is required. |
| Payroll slip view | Information access | Do not treat as signed receipt unless approved. |
| Employment contract/addendum | Formal legal document | Use Kazakhstan-compliant EDS or approved paper process. |

If the company wants legally significant electronic HR documents, add a separate EDS integration track:

- National Certification Authority or other approved signing provider.
- Signed document format and verification.
- Signature certificate validation.
- Long-term archive and verification procedure.
- Revocation and timestamping.

## 12. Retention and Deletion Baseline

Final retention periods must be approved by legal/HR. Until then, implement configurable retention.

| Data | Suggested baseline | Notes |
|---|---:|---|
| Refresh tokens | Until expiry + 30 days | Keep revoked token hash for theft detection. |
| Login/security logs | 1 year | Longer if required by security policy. |
| Audit log for HR/admin actions | 3 years minimum | Current TZ already proposes 3 years. |
| Raw Hikvision payloads | 30-90 days | Keep normalized timesheet longer. |
| Attendance/timesheet | HR/payroll retention period | Confirm with legal/HR. |
| Vacation requests | HR retention period | Do not delete while employment disputes are possible. |
| Sick leave metadata | HR/legal retention period | Restrict access after operational period. |
| Sick leave uploaded scans | HR/legal retention period | Consider archival tier and strict access. |
| 1C sync snapshots | Latest state + short error history | Avoid duplicate long-term storage. |
| Sentry events | 30-90 days | Must be scrubbed of PII. |
| Loki application logs | 30 days | No PII by design. |
| Backups | According to backup policy | Encrypt and test deletion/expiry. |

Deletion requirements:

- Support hard deletion or anonymization for data collected unlawfully or by mistake.
- Support employee data blocking where a dispute or legal hold exists.
- Deletion must cover Postgres, object storage, logs where feasible, search indexes, caches, and backups by expiry.
- Deletion actions must be audited.

## 13. Logging, Monitoring, and Analytics

Logs must be useful for operations but not become a shadow database of personal data.

Do not log:

- Passwords, tokens, refresh token hashes.
- IIN, identity documents, medical details.
- Full sick leave document keys if they reveal employee identity.
- Payroll values.
- Full request/response bodies for HR endpoints.
- Presigned URLs.

Log instead:

- Request ID, route template, status, latency.
- Internal user ID where needed.
- Action code and target ID for audit events.
- Error code, not sensitive payload.

Sentry:

- Enable PII scrubbing.
- Strip request bodies for `/auth`, `/sick-leaves`, `/payroll`, `/employees`.
- Send release SHA and route, not personal content.

Analytics:

- Avoid product analytics in MVP.
- If added later, use anonymized/aggregated metrics and legal review.

## 14. Security Controls Required for Production

Minimum controls:

- TLS 1.2+ and HSTS.
- Password hashing with bcrypt or Argon2id.
- Access token short TTL; refresh token rotation and reuse detection.
- Field-level encryption for IIN and other identity data.
- Private MinIO buckets.
- Presigned URLs with short TTL.
- Antivirus/malware scanning for uploads.
- Rate limiting for auth and upload endpoints.
- CSRF protection for cookie-based refresh flows and critical browser actions.
- Separate production secrets outside Git.
- Encrypted backups.
- Quarterly restore test.
- Role-based access control enforced in backend.
- Audit log for privileged and HR actions.
- Production OpenAPI/docs disabled or behind admin auth.
- Security headers in Nginx.
- Dependency scanning for Python and Node.

Recommended later:

- MFA for admin/HR.
- Device/session management for all users.
- Security review or penetration test before production.
- Data export tool for subject access requests.
- Automated retention jobs.
- Dedicated Redis for queues/streams separate from cache.

## 15. Incident Response

Define this before production:

1. Detection: Sentry, Grafana alerts, suspicious audit events, support reports.
2. Triage: classify whether personal data, medical data, credentials, or files are affected.
3. Containment: revoke sessions, disable affected integration, rotate secrets, block public URLs.
4. Evidence: preserve relevant logs and audit records.
5. Legal assessment: decide whether regulator/employee/customer notification is required.
6. Remediation: patch, rotate, delete exposed objects, restore from backup if needed.
7. Postmortem: root cause, timeline, preventive controls.

Engineering requirement: implement an emergency admin action to revoke all sessions for one user or all users.

## 16. Documents and UI Text Needed Before Launch

Required:

- Privacy notice for employees.
- Personal data consent text, if consent is used.
- Terms of portal use or internal portal policy.
- Internal role/access policy.
- Data retention policy.
- Incident response runbook.
- Backup and restore runbook.
- Administrator operations manual.
- 1C integration data exchange agreement/specification.
- Hikvision attendance data usage policy.
- Vendor/processor list.

Recommended in-app screens:

- "Privacy and data processing" page in profile.
- "My sessions/devices" page.
- "Download my basic profile data" or support request route.
- "Request correction" workflow for profile/timesheet data.

## 17. Engineering Backlog Items from Legal Review

Add these items to the product backlog:

- `consent_records` table: user, version, text_hash, accepted_at, ip, user_agent, revoked_at.
- `data_processing_requests` table: access/correction/blocking/deletion requests.
- `file_access_log` table or audit action for every sick leave document preview/download.
- `hr_location_assignments` table from the main TZ.
- `holidays` and `work_schedules` tables for legally consistent vacation/timesheet calculation.
- Field-level encryption helper for IIN.
- PII scrubber middleware for logs and Sentry.
- Upload malware scan job.
- Configurable retention jobs for raw attendance payloads and old logs.
- Admin report: last 100 privileged actions.
- Data export script for one employee.
- Emergency session revocation endpoint.

## 18. Launch Checklist

- [ ] Data owner/operator and responsible person are named.
- [ ] Privacy notice approved.
- [ ] Consent text approved or statutory basis documented per data category.
- [ ] Data inventory approved.
- [ ] Role/access matrix approved by HR and security.
- [ ] Cross-border transfers reviewed.
- [ ] Production hosting and backups location approved.
- [ ] Sentry/logging PII scrubbing tested.
- [ ] Sick leave access and document audit tested.
- [ ] IIN either excluded from MVP or encrypted/masked.
- [ ] Push notification content reviewed.
- [ ] 1C contracts and payloads approved.
- [ ] Hikvision payload minimization tested.
- [ ] Retention settings configured.
- [ ] Incident response runbook approved.
- [ ] Restore drill completed.
- [ ] Admin access list approved and audited.

## 19. Open Legal Questions

1. Is the portal operated by one legal entity or multiple legal entities?
2. Is employee consent the legal basis for all modules, or do some modules rely on employment/legal obligations?
3. Must personal data and backups be hosted only in Kazakhstan for this company?
4. Are Sentry, Expo, Apple, Google, GitHub, and any CDN approved processors?
5. Can managers see sick leave dates, or only a generic absence status?
6. Is the uploaded sick leave scan sufficient, or must original/eGov verification be integrated?
7. Are vacation requests/approvals legally binding inside the portal, or must they be duplicated in 1C/paper/EDS?
8. What are the exact retention periods for HR, attendance, medical, payroll, audit, and logs?
9. Are biometric templates/photos present in Hikvision payloads?
10. What is the formal procedure for correcting attendance errors?
11. Should admins be allowed to see payroll/sick leave documents, or only HR within scope?
12. Which interface languages are legally required for employee notices: Russian, Kazakh, English?

