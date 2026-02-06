# S3 Upload: Fix "Access Denied" (PutObject)

## What the error means

**`AccessDenied` when calling PutObject** means the AWS credentials your backend uses (from `.env` or default profile) do **not** have permission to upload objects to the S3 bucket.

The IAM user or role that corresponds to `AWS_ACCESS_KEY` / `AWS_SECRET_ACCESS_KEY` needs explicit S3 permissions on your bucket.

---

## Fix: Add IAM policy for the bucket

Attach a policy to the **IAM user** (or role) that your app uses. Replace `YOUR-BUCKET-NAME` with your actual bucket name (e.g. `claim-documents-poc-utsavgohel-auto-insurance-company-ltd`).

### Option 1: Inline policy (AWS Console)

1. Open **IAM** → **Users** → select the user your app uses.
2. **Add permissions** → **Create inline policy** → **JSON**.
3. Paste the policy below (replace `YOUR-BUCKET-NAME`).
4. **Review** → name it e.g. `ClaimDocumentsS3Access` → **Create policy**.

### Option 2: Policy JSON

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ClaimDocumentsUpload",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/claims/*"
    },
    {
      "Sid": "ClaimDocumentsRead",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET-NAME",
        "arn:aws:s3:::YOUR-BUCKET-NAME/*"
      ]
    }
  ]
}
```

- **claims/***: uploads go to `claims/<claim_id>/<filename>`. Restricting to `claims/*` limits access to that prefix.
- **PutObject / PutObjectAcl**: needed for uploads.
- **GetObject / ListBucket**: needed if you later read or list objects from the same bucket.

If you prefer to allow all actions on the bucket (simpler but broader):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET-NAME",
        "arn:aws:s3:::YOUR-BUCKET-NAME/*"
      ]
    }
  ]
}
```

---

## Check your setup

1. **Bucket name**  
   Must match `BUCKET_NAME` in your `.env` (e.g. `claim-documents-poc-utsavgohel-auto-insurance-company-ltd`).

2. **Credentials**  
   The IAM user that has the access key in `.env` must have the policy above (with that bucket name).

3. **Region**  
   Your app uses `AWS_REGION` from `.env`. The bucket must be in that region (or use the bucket’s region in your S3 client if you use a different region).

4. **Bucket policy (optional)**  
   If the bucket has a bucket policy that explicitly **Denies** your IAM user/role, you must update or remove that deny. Default buckets have no such policy.

---

## After updating IAM

- No code change needed.
- Wait a short time for IAM changes to apply (usually seconds).
- Restart the backend if it was running, then try the form upload again.

If you still see **Access Denied**, double-check:
- The bucket name in the policy matches `BUCKET_NAME` in `.env`.
- The access key in `.env` belongs to the IAM user that has this policy.
