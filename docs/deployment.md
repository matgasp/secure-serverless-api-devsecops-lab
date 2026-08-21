# Deployment and operations

## Cost and safety notice

Terraform creates billable AWS resources. WAF is optional and disabled by default. Use a dedicated sandbox account, review `terraform plan`, apply a budget, and run `terraform destroy` when finished.

## Prerequisites

- An AWS account and region.
- A private, encrypted, versioned S3 bucket for Terraform state.
- A GitHub OIDC provider and an AWS role trusted only by the intended repository and protected environment.
- A protected GitHub Environment named `dev`, `staging`, or `production`.

Configure these GitHub values:

| Location | Name | Purpose |
| --- | --- | --- |
| Repository variable | `AWS_REGION` | Deployment region |
| Environment secret | `AWS_ROLE_ARN` | OIDC deployment role |
| Environment secret | `TF_STATE_BUCKET` | Terraform state bucket |

Do not store AWS access keys in GitHub. The deploy workflow exchanges the GitHub OIDC token for short-lived AWS credentials.

## State model

Local live tests use Terraform's default local backend and keep state in `infra/terraform.tfstate`. GitHub workflows generate an S3 backend declaration at runtime and use the environment-specific key `secure-serverless-api/<environment>/terraform.tfstate`.

Do not mix these state locations for the same deployment. Resources created locally must be destroyed locally. Resources created by `Deploy AWS` must be destroyed by `Destroy AWS` using the same GitHub Environment.

## First deployment

1. Review the Terraform files and account-global API Gateway logging role behavior.
2. Run the `CI`, `CodeQL SAST`, and `Terraform IaC` workflows.
3. Open `Deploy AWS` in GitHub Actions and select `dev`.
4. Leave WAF disabled for the first low-cost lab deployment.
5. Approve the protected environment after reviewing the workflow and plan intent.
6. Record the `api_base_url`, Cognito pool ID, and client ID from Terraform outputs.

The deployment summary also records the non-sensitive Terraform outputs. WAF remains disabled unless the manual workflow input explicitly enables it.

## Create test identities

Create two ordinary users and one administrator in the lab user pool. Add only the administrator to the `admin` group. The application client permits SRP for users and IAM-authorized admin password authentication for controlled testing. Do not place passwords or tokens in repository files or command history.

For DAST, configure a protected `dast` GitHub Environment:

| Type | Name | Required |
| --- | --- | --- |
| Variable | `DAST_TARGET_URL` | Yes |
| Secret | `DAST_USER_TOKEN` | For authenticated checks |
| Secret | `DAST_OTHER_USER_TOKEN` | For BOLA check |
| Variable | `DAST_LICENSE_ID` | For BOLA check; must belong to the first user |

The DAST script performs only reads and invalid create attempts. It does not delete data or run a denial-of-service test.

## Repository settings

- Protect `main` and require pull requests.
- Require CI, CodeQL, dependency review, and Terraform checks.
- Enable GitHub secret scanning and push protection when available.
- Restrict environment approval to trusted reviewers.
- Restrict workflow token permissions to the defaults committed here.

## Teardown

### Local deployment

From `infra`, use the same `terraform.tfvars` and local state that created the lab:

```powershell
terraform plan -destroy -out=destroy.tfplan -var-file=terraform.tfvars -var="enable_waf=true"
terraform apply destroy.tfplan
terraform state list
```

The final command must return no resources. Preserve the state until destruction succeeds.

### GitHub deployment

Run the manual `Destroy AWS` workflow, select the same environment used for deployment, and type `destroy` in the confirmation input. The workflow rebuilds the Lambda ZIP required during Terraform evaluation, initializes the same S3 state key, creates a destroy plan, and applies that exact plan.

Cognito deletion protection is intentionally inactive for this lab. The pre-existing S3 state bucket, GitHub OIDC provider, and deployment IAM role are not managed by this Terraform configuration and remain after teardown.
