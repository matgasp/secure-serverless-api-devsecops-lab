# Threat model

## Assets

- License ownership, state, and expiration data.
- Cognito identities and authorization claims.
- AWS deployment role and Terraform state.
- Availability of the validation endpoint.
- Audit and diagnostic records.

## Primary abuse cases and controls

| Threat | Example | Primary controls | Residual risk |
| --- | --- | --- | --- |
| BOLA/IDOR | User A requests User B's UUID | Server-side owner comparison; cross-owner requests return `404`; tests and DAST coverage | Administrator group compromise |
| Privilege escalation | Caller sends another `owner_sub` | Identity comes from verified claims; only `admin` may override owner | Incorrect Cognito group administration |
| Injection or parser abuse | Oversized, malformed, or unexpected JSON | 16 KiB limit, UTF-8 JSON object requirement, allowlisted fields, constrained formats | Novel parser/runtime vulnerabilities |
| Credential leakage | Token appears in code, logs, or artifacts | No payload/header logging; repository secret checks; GitHub secret scanning recommendation; OIDC deploy | Secrets pasted outside controlled paths |
| Dependency compromise | Vulnerable or malicious package enters build | One pinned runtime dependency, `pip-audit`, dependency review, Dependabot, CodeQL | Registry or maintainer compromise |
| IaC misconfiguration | Wildcard IAM or public resource | Fragmented Terraform, custom policy checks, validation, reviewed plan, least privilege | Custom checks do not replace a full cloud review |
| Denial of service or cost abuse | High request volume | API throttling, reserved concurrency, optional WAF rate rule, alarms | Distributed traffic when WAF is disabled |
| Repudiation | User denies a destructive action | Cognito subject, API request ID, structured events, CloudWatch access logs | Log deletion by privileged AWS principal |
| Data exposure in diagnostics | Body or token captured in logs | API data tracing disabled; application logs identifiers only | AWS account administrators can inspect infrastructure |
| Supply-chain workflow abuse | Pull request gains AWS access | Read-only PR permissions; deploy is manual; OIDC and protected environment | Misconfigured repository/environment permissions |

## Security assumptions

- API Gateway passes claims only after Cognito validation.
- Cognito group membership is administered by a trusted operator.
- The state bucket exists, is private, encrypted, versioned, and restricted to the deployment role.
- Branch protection requires successful checks before merge.
- AWS resources are deployed in a dedicated sandbox account for the lab.

## Out of scope

- Browser UI security and CORS.
- Mobile clients and certificate pinning.
- Payment, entitlement issuance policy, and commercial licensing logic.
- Multi-region disaster recovery.
- Red-team evasion or destructive load testing.

## Production hardening backlog

- Enable Cognito deletion protection and threat protection.
- Use a customer-managed KMS key where regulatory requirements justify it.
- Enable WAF and add carefully tuned managed rule groups.
- Add alert destinations, runbooks, SLOs, and log archive controls.
- Add a custom domain, explicit TLS policy, and mTLS where clients support it.
- Add CloudTrail data-event analysis and continuous AWS configuration assessment.
- Conduct an independent penetration test and load test in an authorized environment.
