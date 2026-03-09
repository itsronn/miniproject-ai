import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAssessment } from '../context/AssessmentContext';
import { predictHandwriting } from '../services/api';
import ProgressStepper from '../components/ProgressStepper';
import FileUpload from '../components/FileUpload';

/**
 * Handwriting test: upload image, analyze via API, save risk_score.
 */
export default function HandwritingTest() {
  const { setHandwritingScore } = useAssessment();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileSelect = (selectedFile) => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
    setError('');
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const data = await predictHandwriting(file);
      setHandwritingScore(data.risk_score);
    } catch (err) {
      setError(err.message || 'Analysis failed. Is the backend running at http://localhost:8000?');
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => navigate('/speech');

  return (
    <div className="card">
      <ProgressStepper currentStep="handwriting" />
      <h2>Handwriting test</h2>
      <p className="text-muted">
        Upload a clear photo or scan of a handwriting sample. We recommend lined paper with good contrast.
      </p>
      <FileUpload onFileSelect={handleFileSelect} previewUrl={previewUrl} accept="image/*" />
      {loading && <p className="loading">Loading...</p>}
      {error && <p className="error-msg">{error}</p>}
      <div className="mt-2 actions-row">
        <button type="button" className="btn-primary" onClick={handleAnalyze} disabled={!file || loading}>
          Analyze
        </button>
        <button type="button" className="btn-secondary" onClick={handleContinue}>
          Continue
        </button>
        <Link to="/user">
          <button type="button" className="btn-secondary">Back</button>
        </Link>
      </div>
    </div>
  );
}
