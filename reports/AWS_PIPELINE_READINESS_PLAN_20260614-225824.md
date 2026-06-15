# AWS Pipeline Readiness Plan

## Current VPS AWS State

- AWS CLI installed: yes
- AWS CLI path: /usr/local/bin/aws
- AWS credentials installed: no
- AWS config installed: no
- AWS services running: no
- Cloud resources changed: no

## Correct Role for AWS in Embiz

AWS should remain optional until a specific pipeline need exists.

Recommended future uses:
1. S3 bucket for job archive backups.
2. SES for outbound customer email drafts/sending after approval.
3. Textract/Rekognition only if artwork/image extraction becomes useful.
4. Bedrock only if explicitly chosen over current Claude/OpenAI setup.
5. CloudWatch only if we want cloud logging later.

## Do Not Do Yet

- Do not copy laptop ~/.aws credentials blindly.
- Do not enable automatic customer email sending.
- Do not add AWS as a dependency for intake.
- Do not create buckets, SES identities, IAM users, or Bedrock permissions until the use case is chosen.

## Immediate Next Step

Finish Embiz Phase 1 local orchestration first:
- Worker payload/header fix
- job watcher
- Slack notifications
- pipeline task folders
- specialized agent instructions
- validation report

AWS can be added after the local pipeline is stable.
