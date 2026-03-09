import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAssessment } from '../context/AssessmentContext';
import { predictCognitive } from '../services/api';
import ProgressStepper from '../components/ProgressStepper';
import ReactionTest from '../components/ReactionTest';

/**
 * Cognitive test: reaction time. Send metrics to API, save risk_score.
 */
export default function CognitiveTest() {
  const { setCognitiveScore } = useAssessment();
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleReactionComplete = (m) => setMetrics(m);

  const handleAnalyze = async () => {
    if (!metrics) return;
    setLoading(true);
    setError('');
    try {
      const data = await predictCognitive(metrics);
      setCognitiveScore(data.risk_score);
    } catch (err) {
      setError(err.message || 'Analysis failed. Is the backend running at http://localhost:8000?');
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => navigate('/report');

  return (
    <div className="card">
      <ProgressStepper currentStep="cognitive" />
      <h2>Cognitive test</h2>
      <p className="text-muted">
        A simple reaction-time task. Click when ready, then respond as soon as the button changes state.
      </p>
      <ReactionTest onComplete={handleReactionComplete} />
      {metrics && (
        <>
          <p className="text-muted" style={{ marginTop: '1rem' }}>Average reaction time: {metrics.averageMs} ms</p>
          {loading && <p className="loading">Loading...</p>}
          {error && <p className="error-msg">{error}</p>}
          <div className="mt-2 actions-row">
            <button type="button" className="btn-primary" onClick={handleAnalyze} disabled={loading}>
              Analyze
            </button>
            <button type="button" className="btn-secondary" onClick={handleContinue}>
              Continue
            </button>
          </div>
        </>
      )}
      <div className="mt-2">
        <Link to="/eye">
          <button type="button" className="btn-secondary">Back</button>
        </Link>
      </div>
    </div>
  );
}
