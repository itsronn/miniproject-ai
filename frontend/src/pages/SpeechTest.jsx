import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAssessment } from '../context/AssessmentContext';
import { predictSpeech } from '../services/api';
import ProgressStepper from '../components/ProgressStepper';
import AudioRecorder from '../components/AudioRecorder';

/**
 * Speech test: record audio, send to API, save risk_score.
 */
export default function SpeechTest() {
  const { setSpeechScore } = useAssessment();
  const navigate = useNavigate();
  const [audioBlob, setAudioBlob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRecordingComplete = (blob) => {
    setAudioBlob(blob);
    setError('');
  };

  const handleAnalyze = async () => {
    if (!audioBlob) return;
    setLoading(true);
    setError('');
    try {
      const data = await predictSpeech(audioBlob);
      setSpeechScore(data.risk_score);
    } catch (err) {
      setError(err.message || 'Analysis failed. Is the backend running at http://localhost:8000?');
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => navigate('/eye');

  return (
    <div className="card">
      <ProgressStepper currentStep="speech" />
      <h2>Speech test</h2>
      <p className="text-muted">Read the prompt in a natural voice, then record once you&apos;re ready.</p>
      <p className="speech-prompt">
        "The quick brown fox jumps over the lazy dog. She sells seashells by the seashore."
      </p>
      <AudioRecorder onRecordingComplete={handleRecordingComplete} />
      {audioBlob && <p className="text-muted" style={{ marginTop: '0.5rem' }}>Recording ready. Click Analyze to send.</p>}
      {loading && <p className="loading">Loading...</p>}
      {error && <p className="error-msg">{error}</p>}
      <div className="mt-2 actions-row">
        <button type="button" className="btn-primary" onClick={handleAnalyze} disabled={!audioBlob || loading}>
          Analyze
        </button>
        <button type="button" className="btn-secondary" onClick={handleContinue}>
          Continue
        </button>
        <Link to="/handwriting">
          <button type="button" className="btn-secondary">Back</button>
        </Link>
      </div>
    </div>
  );
}
