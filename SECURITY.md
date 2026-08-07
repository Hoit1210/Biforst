# Security

This repository is a portfolio implementation and must not contain live credentials.

## Never commit

- Discord webhook URLs
- Gemini API keys
- GitHub personal access tokens
- AWS access keys or secret keys
- real EC2 public IPs when they are not needed for documentation
- account-specific secrets, passwords, or private certificates

Use `.env` locally and keep only `.env.example` in Git.

## AWS credentials

The current code uses the standard boto3 credential provider chain rather than hard-coded access keys. In AWS, prefer an EC2 Instance Profile, ECS Task Role, or other workload identity with only the permissions required for CloudWatch and the configured WAFv2 IP Set.

## Approval endpoint

The `/action` query-link workflow is a prototype used to validate Human-in-the-loop control. A production implementation should add HTTPS, authentication, signed/expiring actions, authorization, replay protection, audit logging, and CSRF-aware interaction design.

## Historical secrets

Removing a secret from the current branch does not remove it from Git history. If any credential was committed previously, revoke or rotate it. For sensitive public-history cleanup, use GitHub-supported history rewriting procedures and coordinate before force-pushing shared branches.

## Reporting

This is a personal portfolio repository. Do not open a public issue containing a credential or sensitive value.
