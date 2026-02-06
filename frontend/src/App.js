import { useState } from 'react';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

function App() {
  const [mode, setMode] = useState('paste'); // 'paste' | 'form'
  const [claimText, setClaimText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form state
  const [form, setForm] = useState({
    claim_id: '',
    driver_name: '',
    incident_date: '',
    filing_date: '',
    incident_description: '',
    damages: '',
    request: '',
  });
  const [policeReportFile, setPoliceReportFile] = useState(null);
  const [crashPhotoFile, setCrashPhotoFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');

  const loadSample = async (name) => {
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/samples/${name}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || res.statusText);
      setClaimText(data.claim_text || '');
      setResult(null);
    } catch (e) {
      setError(e.message);
    }
  };

  const buildClaimTextFromForm = () => {
    const lines = [
      'CLAIM FORM',
      `Claim ID: ${form.claim_id || '[Not provided]'}`,
      `Date of Incident: ${form.incident_date || '[Not provided]'}`,
      `Date of Filing: ${form.filing_date || '[Not provided]'}`,
      `Driver Name: ${form.driver_name || '[Not provided]'}`,
      '',
      'Incident Description:',
      form.incident_description || '[Not provided]',
      '',
      'Damages:',
      form.damages || '[Not provided]',
      '',
      'Request:',
      form.request || '[Not provided]',
    ];
    return lines.join('\n');
  };

  const uploadFileToS3 = async (file, claimId) => {
    const res = await fetch(
      `${API_BASE}/api/upload-url?claim_id=${encodeURIComponent(claimId)}&filename=${encodeURIComponent(file.name)}`
    );
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `Failed to get upload URL (${res.status})`);
    const putRes = await fetch(data.upload_url, {
      method: 'PUT',
      body: file,
      headers: { 'Content-Type': file.type || 'application/octet-stream' },
    });
    if (!putRes.ok) throw new Error('Upload failed');
  };

  const submitForm = async () => {
    const claimId = form.claim_id.trim() || 'form-claim';
    const text = buildClaimTextFromForm();
    if (!text.trim() || !form.driver_name.trim()) {
      setError('Please fill in at least Driver name and Incident description.');
      return;
    }
    setError(null);
    setUploadStatus('');
    setLoading(true);
    setResult(null);
    try {
      if (policeReportFile || crashPhotoFile) {
        setUploadStatus('Uploading files to S3…');
        try {
          if (policeReportFile) await uploadFileToS3(policeReportFile, claimId);
          if (crashPhotoFile) await uploadFileToS3(crashPhotoFile, claimId);
          setUploadStatus('Files uploaded. Processing claim…');
        } catch (uploadErr) {
          if (uploadErr.message?.includes('503') || uploadErr.message?.toLowerCase().includes('not configured')) {
            setUploadStatus('S3 not configured; processing claim text only.');
          } else {
            throw uploadErr;
          }
        }
      }
      const res = await fetch(`${API_BASE}/api/process-claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ claim_text: text }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || res.statusText);
      setResult(data);
      setUploadStatus('');
    } catch (e) {
      setError(e.message);
      setUploadStatus('');
    } finally {
      setLoading(false);
    }
  };

  const submitClaim = async () => {
    if (!claimText.trim()) {
      setError('Enter or load claim text first.');
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/process-claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ claim_text: claimText }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || res.statusText);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusClass = (status) => {
    if (status === 'APPROVED') return 'status-approved';
    if (status === 'DENIED') return 'status-denied';
    return 'status-review';
  };

  const getVerificationClass = (status) => {
    if (status === 'VERIFIED') return 'verification-verified';
    if (status === 'SUSPICIOUS') return 'verification-suspicious';
    return 'verification-review';
  };

  const updateForm = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Auto Insurance FNOL — Claim Check</h1>
        <p className="subtitle">
          Compare a claim against your policy. Paste claim text or use the form and upload documents, then submit to see the outcome.
        </p>
        <div className="steps">
          <span className="step">1. Load, paste or fill form</span>
          <span className="step-arrow">→</span>
          <span className="step">2. Submit</span>
          <span className="step-arrow">→</span>
          <span className="step">3. See result</span>
        </div>
      </header>

      <main className="App-main">
        <div className="tabs">
          <button
            type="button"
            className={`tab ${mode === 'paste' ? 'active' : ''}`}
            onClick={() => setMode('paste')}
          >
            Paste claim
          </button>
          <button
            type="button"
            className={`tab ${mode === 'form' ? 'active' : ''}`}
            onClick={() => setMode('form')}
          >
            Form + upload
          </button>
        </div>

        <div className="two-col">
          <section className="panel claim-panel">
            <h2 className="panel-title">Claim</h2>
            {mode === 'paste' && (
              <>
                <p className="panel-hint">Load a sample or paste claim text below.</p>
                <div className="sample-buttons">
                  <button type="button" onClick={() => loadSample('claim_valid')}>
                    Happy Path (CL-2024-001)
                  </button>
                  <button type="button" onClick={() => loadSample('claim_invalid')}>
                    Rejection (CL-2024-002)
                  </button>
                </div>
                <textarea
                  value={claimText}
                  onChange={(e) => setClaimText(e.target.value)}
                  placeholder="Paste claim text here or use a sample above."
                  rows={16}
                  disabled={loading}
                />
                <button
                  type="button"
                  className="submit-btn"
                  onClick={submitClaim}
                  disabled={loading || !claimText.trim()}
                >
                  {loading ? 'Checking claim…' : 'Compare against policy'}
                </button>
              </>
            )}
            {mode === 'form' && (
              <>
                <p className="panel-hint">Fill in the details. You can upload a police report and crash photo (uploaded to S3 if configured).</p>
                <div className="form-row">
                  <label className="gds-label" htmlFor="claim_id">Claim ID</label>
                  <input
                    id="claim_id"
                    type="text"
                    className="gds-input"
                    value={form.claim_id}
                    onChange={(e) => updateForm('claim_id', e.target.value)}
                    placeholder="e.g. CL-2024-001"
                    disabled={loading}
                  />
                </div>
                <div className="form-row">
                  <label className="gds-label" htmlFor="driver_name">Driver name</label>
                  <input
                    id="driver_name"
                    type="text"
                    className="gds-input"
                    value={form.driver_name}
                    onChange={(e) => updateForm('driver_name', e.target.value)}
                    disabled={loading}
                  />
                </div>
                <div className="form-row">
                  <label className="gds-label" htmlFor="incident_date">Date of incident</label>
                  <input
                    id="incident_date"
                    type="text"
                    className="gds-input"
                    value={form.incident_date}
                    onChange={(e) => updateForm('incident_date', e.target.value)}
                    placeholder="e.g. 2024-02-10"
                    disabled={loading}
                  />
                </div>
                <div className="form-row">
                  <label className="gds-label" htmlFor="filing_date">Date of filing</label>
                  <input
                    id="filing_date"
                    type="text"
                    className="gds-input"
                    value={form.filing_date}
                    onChange={(e) => updateForm('filing_date', e.target.value)}
                    placeholder="e.g. 2024-02-12"
                    disabled={loading}
                  />
                </div>
                <div className="form-row">
                  <label className="gds-label" htmlFor="incident_description">Incident description</label>
                  <textarea
                    id="incident_description"
                    className="gds-textarea"
                    value={form.incident_description}
                    onChange={(e) => updateForm('incident_description', e.target.value)}
                    placeholder="Describe what happened."
                    disabled={loading}
                  />
                </div>
                <div className="form-row">
                  <label className="gds-label" htmlFor="damages">Damages</label>
                  <textarea
                    id="damages"
                    className="gds-textarea"
                    value={form.damages}
                    onChange={(e) => updateForm('damages', e.target.value)}
                    placeholder="Estimated cost, police report, etc."
                    disabled={loading}
                  />
                </div>
                <div className="form-row">
                  <label className="gds-label" htmlFor="request">Request</label>
                  <input
                    id="request"
                    type="text"
                    className="gds-input"
                    value={form.request}
                    onChange={(e) => updateForm('request', e.target.value)}
                    placeholder="e.g. Collision claim and rental car"
                    disabled={loading}
                  />
                </div>
                <div className="file-input-wrap">
                  <label className="gds-label">Police report (PDF or image)</label>
                  <input
                    type="file"
                    accept=".pdf,image/*"
                    onChange={(e) => setPoliceReportFile(e.target.files?.[0] || null)}
                    disabled={loading}
                  />
                  {policeReportFile && <div className="file-list">Selected: {policeReportFile.name}</div>}
                </div>
                <div className="file-input-wrap">
                  <label className="gds-label">Crash photo</label>
                  <input
                    type="file"
                    accept="image/*,.pdf"
                    onChange={(e) => setCrashPhotoFile(e.target.files?.[0] || null)}
                    disabled={loading}
                  />
                  {crashPhotoFile && <div className="file-list">Selected: {crashPhotoFile.name}</div>}
                </div>
                {uploadStatus && <p className="upload-status">{uploadStatus}</p>}
                <button
                  type="button"
                  className="submit-btn"
                  onClick={submitForm}
                  disabled={loading}
                >
                  {loading ? 'Checking claim…' : 'Compare against policy'}
                </button>
              </>
            )}
            {error && <div className="error">{error}</div>}
          </section>

          <section className="panel result-panel">
            <h2 className="panel-title">Result</h2>
            {loading && (
              <div className="loader-wrap">
                <div className="loader" />
                <p className="loader-text">Your claim is under review</p>
                <p className="loader-sub">Comparing against policy rules.</p>
              </div>
            )}
            {!loading && !result && (
              <div className="result-placeholder">
                <div className="placeholder-icon">📋</div>
                <p>Result will appear here</p>
                <p className="placeholder-hint">Use paste or form, then submit to see status, reasoning and extracted data.</p>
              </div>
            )}
            {!loading && result && (
              <div className="result-content">
                <div className={`status-badge ${getStatusClass(result.status)}`}>
                  {result.status}
                </div>
                {result.claim_id && <p className="result-claim-id">Claim: {result.claim_id}</p>}
                
                {result.verification && (
                  <div className="result-block verification-block">
                    <h3>Document Verification</h3>
                    <div className={`verification-badge ${getVerificationClass(result.verification.verification_status)}`}>
                      {result.verification.verification_status}
                    </div>
                    <p className="verification-recommendation">{result.verification.recommendation}</p>
                    {result.verification.confidence_score && (
                      <p className="verification-confidence">
                        Confidence: {Math.round(result.verification.confidence_score * 100)}%
                      </p>
                    )}
                    {result.verification.checks && result.verification.checks.length > 0 && (
                      <details className="verification-details">
                        <summary>
                          View verification checks ({result.verification.summary?.passed || 0} passed, {result.verification.summary?.failed || 0} failed, {result.verification.summary?.warnings || 0} warnings)
                        </summary>
                        <ul className="verification-checks">
                          {result.verification.checks.map((check, idx) => (
                            <li key={idx} className={`check-${check.status?.toLowerCase() || 'skip'}`}>
                              <strong>{check.check || 'Unknown'}:</strong> {check.status || 'SKIP'} — {check.details || ''}
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </div>
                )}
                
                {result.reasoning && (
                  <div className="result-block">
                    <h3>Reasoning</h3>
                    <p>{result.reasoning}</p>
                  </div>
                )}
                {result.extracted_data && (
                  <div className="result-block">
                    <h3>Extracted data</h3>
                    <pre>{JSON.stringify(result.extracted_data, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
