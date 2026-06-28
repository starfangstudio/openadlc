---
name: iac
description: "This skill should be used when provisioning or changing cloud infrastructure as code, \"set up Terraform\", \"add a Pulumi stack\", \"write a CDK app\", \"configure remote state\", \"add state locking\", \"split infra per environment\", \"create a reusable module\", \"review this terraform plan\", \"detect drift\", \"is my infra idempotent\", or reviewing IaC changes. Detect-first across Terraform, Pulumi, and AWS CDK: remote state with locking, reusable modules, per-environment isolation, and the plan / review / apply discipline (apply is outbound and needs the operator's explicit yes first). Routes observability to adlc-ops, security hardening to adlc-security, data modeling to adlc-database."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Infrastructure as code

Provision infrastructure declaratively, in the tool the repo already uses, with state that is remote, locked, and never holding secrets. The plan is the artifact you review; the apply is an outbound act that needs consent.

## Step 1: Detect the tool first
Never impose a stack. Look for the marker files before writing anything:
- **Terraform / OpenTofu:** `*.tf`, a `terraform { }` block, `.terraform.lock.hcl`, `*.tfvars`. (OpenTofu is the open-source fork; same HCL, the `tofu` CLI.)
- **Pulumi:** `Pulumi.yaml` (project) and `Pulumi.<stack>.yaml` (per-stack config); program in TypeScript / Python / Go / .NET.
- **AWS CDK:** `cdk.json` and an `app` entrypoint; stacks defined in TypeScript / Python / Java / Go, synthesized to CloudFormation.

Match the detected tool, its layout, and its naming. If the repo has no IaC yet, ask which tool before scaffolding; do not pick for the team. Note: CDK for Terraform (CDKTF) was archived in December 2025, so do not start new work on it.

## Step 2: Remote state, with locking (never local, never committed)
State is the source of truth for what exists. Keep it remote and locked so two applies cannot race.
- **Terraform / OpenTofu (`s3` backend):** enable bucket versioning, then set `use_lockfile = true` for native S3 lock files. This is GA since Terraform 1.11 and replaces the old DynamoDB lock table; drop `dynamodb_table` on new setups. GCS and azurerm backends lock natively.
- **Pulumi:** Pulumi Cloud, or a DIY backend (S3 / GCS / Azure Blob) which has file-based locking on by default (a lock object beside the state). No separate lock service needed.
- **CDK:** state lives in the CloudFormation service; `cdk bootstrap` provisions the assets bucket and roles per account+region. Bootstrap each environment before deploying into it.

Never commit a `.tfstate`, a Pulumi state file, or `.tfvars` holding secrets. State is sensitive (it can contain resolved secret values); lock the bucket down and encrypt it.

## Step 3: Reusable modules, per-environment isolation
- **Modules:** factor repeated infra into a module (Terraform `module` / `modules/`, Pulumi component resource, CDK construct). Inputs typed, outputs explicit, one responsibility. Version shared modules (a registry or a pinned git ref); pin provider and module versions so a plan is reproducible.
- **Per environment:** give dev / staging / prod separate state and config so a prod apply can never touch dev.
  - Terraform: a directory or backend key per env (preferred for strong isolation), or CLI workspaces for lighter cases.
  - Pulumi: one **stack** per env, config in `Pulumi.<stack>.yaml`.
  - CDK: one **Stage** (or env-scoped stack) per env, with explicit `env: { account, region }`.

## Step 4: The plan / review / apply discipline
The plan is the reviewable diff. Read it before anything changes.
- Generate and **save** the plan: Terraform `terraform plan -out=tfplan`; Pulumi `pulumi preview`; CDK `cdk diff`.
- Review the diff like code: what is created, **changed**, and especially **destroyed or replaced**. A replace on a stateful resource (database, volume) is a data-loss risk; stop and confirm intent.
- **Apply is outbound: get the operator's explicit yes first.** `terraform apply`, `pulumi up`, and `cdk deploy` create or destroy real cloud resources and cost money. Finish locally, present exactly what will change (the saved plan), and wait for an explicit yes before applying. Apply the saved plan, not a fresh re-plan, so what ships equals what was reviewed.

## Step 5: Drift detection
Drift is reality diverging from code (a console hotfix, an out-of-band change). Catch it, do not let it accumulate.
- **Terraform / OpenTofu:** `terraform plan -refresh-only -detailed-exitcode`. Exit `0` = no drift, `2` = drift detected, `1` = error. Wire that exit code into a scheduled check.
- **Pulumi:** `pulumi preview --refresh` (or `pulumi refresh` to reconcile state).
- **CDK:** `cdk drift` reports resources changed outside CloudFormation; `cdk diff` shows code-vs-deployed.

Reconcile drift by codifying the change and re-applying, not by hand-editing again.

## Step 6: No secrets in state or code
- Never hardcode keys, passwords, or tokens in `.tf` / program files or `.tfvars`. Reference a secret manager (AWS Secrets Manager, Vault, SSM Parameter Store, Pulumi config secrets, GCP Secret Manager) and pass values at apply time.
- Mark sensitive inputs/outputs (`sensitive = true`, Pulumi secret config) so they do not print in plan output or logs.
- For hardening of IAM, network policy, encryption posture, and secret-store choice, route to **adlc-security** rather than deciding it here.

## Boundaries (route, do not duplicate)
- **Observability / monitoring / alerting / CI-CD pipeline authoring:** `adlc-ops`. (This skill stops at running the IaC tool; pipeline wiring is ops.)
- **Security hardening (IAM least-privilege, network/firewall rules, encryption, secret-store selection):** `adlc-security`.
- **Data modeling, schemas, migrations, query design:** `adlc-database`. Provisioning the database server/cluster is in scope here; what is inside it is not.
- **Containers and Kubernetes manifests:** sibling skills `containers` and `orchestration` in this pack.

## References
- Terraform S3 native state locking (`use_lockfile`, GA in 1.11): https://developer.hashicorp.com/terraform/language/backend/s3
- Terraform drift via `-detailed-exitcode`: https://developer.hashicorp.com/terraform/cli/commands/plan
- Pulumi state and backends (DIY locking, stacks per env): https://www.pulumi.com/docs/iac/concepts/state-and-backends/
- AWS CDK bootstrapping and deploy: https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html
- Sibling skills: `containers`, `orchestration`. Routes: `adlc-ops`, `adlc-security`, `adlc-database`.

## The check (failable)
After an approved apply, the plan must be **clean and idempotent**: run the plan again and it shows **no changes**.
- Terraform / OpenTofu: `terraform plan -detailed-exitcode` exits `0`.
- Pulumi: `pulumi preview` reports no changes (the diff is empty).
- CDK: `cdk diff` reports no differences.

A second plan that still wants to change things means the config is not converged (a non-idempotent resource, a missing `lifecycle`/ignore, or unmanaged drift). It is not done until the re-plan is empty.
