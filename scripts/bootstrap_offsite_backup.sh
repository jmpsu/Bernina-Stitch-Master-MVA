#!/usr/bin/env bash
# bootstrap_offsite_backup.sh — run ON THE OPERATOR'S MACHINE to inventory,
# back up, and upload to S3 in one command. This does NOT run inside the
# ephemeral cloud session (that container is not your machine and has no
# valid AWS credentials); it is the executable handoff for the machine that
# actually holds the files.
#
# Usage:
#   scripts/bootstrap_offsite_backup.sh s3://your-bucket/embiz [--allow-root]
#
# Credentials are read from the standard AWS chain (env vars or ~/.aws);
# never passed on the command line, never written to the repo.
#
# Safety: if the resolved AWS identity is the ACCOUNT ROOT, the script stops
# and refuses to upload unless --allow-root is given. Root access keys should
# be rotated and replaced with a scoped IAM user (see the printed guidance).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
S3_URL="${1:-}"
ALLOW_ROOT="${2:-}"

if [[ -z "$S3_URL" || "$S3_URL" != s3://* ]]; then
  echo "usage: $0 s3://bucket/prefix [--allow-root]" >&2
  exit 64
fi

echo "== 1/4 preflight: AWS identity =="
if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI not found — install it or run scripts/backup_machine.py --upload directly (boto3)." >&2
  exit 69
fi
IDENTITY_ARN="$(aws sts get-caller-identity --query Arn --output text)"
echo "identity: $IDENTITY_ARN"
if [[ "$IDENTITY_ARN" == *":root" ]]; then
  echo "" >&2
  echo "!! This is the AWS ACCOUNT ROOT identity." >&2
  echo "!! A root access key was found in plaintext on this machine" >&2
  echo "!! (Downloads/rootkey.csv and copies). Using it for backups is a" >&2
  echo "!! standing risk. Recommended before proceeding:" >&2
  echo "!!   1. aws iam create-user --user-name embiz-backup" >&2
  echo "!!   2. attach a policy scoped to just this bucket (see below)" >&2
  echo "!!   3. create an access key for that user; configure a named profile" >&2
  echo "!!   4. DELETE the root access key in the IAM console" >&2
  if [[ "$ALLOW_ROOT" != "--allow-root" ]]; then
    echo "Refusing to upload with root credentials. Re-run with --allow-root to override." >&2
    exit 77
  fi
  echo "(--allow-root given: proceeding against advice)"
fi

echo "== 2/4 machine inventory =="
EMBIZ_SCAN_ROOTS="${EMBIZ_SCAN_ROOTS:-$HOME:/opt:/srv}" \
  python3 "$REPO/tools/machine_inventory.py"

echo "== 3/4 local verified backup =="
python3 "$REPO/scripts/backup_machine.py"

echo "== 4/4 upload latest backup to $S3_URL =="
python3 "$REPO/scripts/backup_machine.py" --upload "$S3_URL"

cat <<'POLICY'

--- Example least-privilege bucket policy for the embiz-backup IAM user ---
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject", "s3:ListBucket"],
    "Resource": ["arn:aws:s3:::YOUR-BUCKET", "arn:aws:s3:::YOUR-BUCKET/embiz/*"]
  }]
}
POLICY
echo "done."
