# Document Verification & Fraud Detection

## The Challenge

**Question:** How is legitimacy identified if the document is not forged?

Insurance claims can include forged documents (fake police reports, altered photos, fabricated claim details). We need to detect:
- **Forged documents** (fake police reports, altered PDFs)
- **Tampered photos** (edited damage photos, reused images)
- **Inconsistent data** (dates don't match, details conflict)
- **Suspicious patterns** (same photo used in multiple claims, unusual timing)

---

## Solutions We Can Build

### 1. **AI-Based Document Analysis** (Using Bedrock + Textract)

**What it checks:**
- **Text consistency:** Does the claim text match the police report? (e.g. dates, location, parties)
- **Format anomalies:** Does the document format match expected templates? (police reports have standard structure)
- **Language patterns:** Does the writing style match official documents? (police reports use formal language)
- **Metadata extraction:** Extract dates, names, locations and cross-check for conflicts

**AWS Services:**
- **Amazon Textract** — Extract text, tables, forms from PDFs/images
- **Amazon Bedrock** — Analyze extracted text for inconsistencies, anomalies, suspicious patterns
- **Amazon Rekognition** — Detect if photos are tampered (duplicate detection, metadata analysis)

**Example flow:**
1. Upload claim + police report PDF
2. Textract extracts text from both
3. Bedrock compares: "Does the police report date match claim incident date? Does location match? Are there contradictions?"
4. Return confidence score: "HIGH_CONFIDENCE", "NEEDS_REVIEW", "SUSPICIOUS"

---

### 2. **Cross-Reference Verification** (External APIs)

**What it checks:**
- **Police report validation:** If police report number provided, verify it exists in police database (if API available)
- **Date logic:** Filing date must be after incident date; incident date must be in the past
- **Policy check:** Verify claim ID format matches company pattern; check if policy number exists

**Implementation:**
- Backend calls external APIs (if available) or internal policy database
- For PoC: Simple rule-based checks (date logic, format validation)

---

### 3. **Image Analysis** (Rekognition + Metadata)

**What it checks:**
- **Photo metadata:** EXIF data (date taken, location, device) — does it match claim date/location?
- **Duplicate detection:** Has this photo been used in another claim? (compare against S3 stored images)
- **Tampering detection:** Signs of editing (inconsistent lighting, cloned areas, metadata stripped)
- **Scene analysis:** Does the photo show damage consistent with the claim description?

**AWS Services:**
- **Amazon Rekognition** — Detect labels, objects, text in images; compare faces/objects
- **S3 + Lambda** — Store image hashes, compare against previous claims

---

### 4. **Anomaly Detection** (Bedrock + Rules)

**What it checks:**
- **Timing anomalies:** Claim filed too quickly after incident? Too late? (policy says 14 days)
- **Cost anomalies:** Repair cost unusually high/low for described damage?
- **Pattern matching:** Same driver name/vehicle appearing frequently? Same photo reused?

**Implementation:**
- Bedrock analyzes claim against historical patterns (if you have data)
- Rule-based checks: "If collision > $2,000 and no police report → FLAG"

---

## Recommended Implementation (For Your PoC)

### Phase 1: Basic Verification (Can Build Now)

1. **Text consistency check** (Bedrock):
   - Compare claim text vs police report text (if uploaded)
   - Check: dates match? Location matches? Driver name matches?
   - Return: "CONSISTENT", "INCONSISTENT", "MISSING_DATA"

2. **Date logic validation** (Rules):
   - Filing date must be after incident date
   - Filing date must be within 14 days (per policy)
   - Incident date must be in the past

3. **Required document check** (Rules):
   - If collision > $2,000 → police report required
   - If missing → flag as "NEEDS_REVIEW"

4. **Format validation** (Rules):
   - Claim ID format matches pattern (e.g. CL-YYYY-NNN)
   - Required fields present (driver name, incident date, etc.)

### Phase 2: Image Analysis (Add Rekognition)

1. **Photo metadata extraction** (EXIF)
2. **Duplicate detection** (compare image hash against S3 stored images)
3. **Basic tampering detection** (Rekognition labels + metadata checks)

### Phase 3: Advanced AI Analysis (Bedrock)

1. **Anomaly detection:** Unusual patterns, suspicious timing
2. **Language analysis:** Does police report sound official? Does claim description match typical patterns?
3. **Cross-document consistency:** Deep comparison of all uploaded documents

---

## Quick Win: Add to Your Current System

**Option A: Simple rule-based verification** (no new AWS services)
- Add verification function to backend
- Check date logic, required docs, format
- Return verification status alongside claim processing result

**Option B: Add Textract + Bedrock verification** (uses existing AWS services)
- Use Textract to extract text from uploaded PDFs
- Use Bedrock to compare claim vs police report for consistency
- Return detailed verification report

**Option C: Add Rekognition for images** (new AWS service)
- Analyze uploaded photos for metadata, duplicates, tampering
- Most comprehensive but requires Rekognition setup

---

## Recommendation

**Start with Option A** (rule-based) — quick to implement, catches common issues:
- Date logic violations
- Missing required documents
- Format errors

**Then add Option B** (Textract + Bedrock) — deeper analysis:
- Cross-document consistency
- Language pattern analysis
- Anomaly detection

**Later add Option C** (Rekognition) — full image verification:
- Photo authenticity
- Duplicate detection
- Tampering detection

This gives you a **verification score** alongside the claim processing result, so users see: "Claim processed. Verification: NEEDS_REVIEW (police report missing for collision > $2,000)."
