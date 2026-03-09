import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAssessment } from '../context/AssessmentContext';
import { predictFinal } from '../services/api';
import ScoreCard from '../components/ScoreCard';
import ProgressStepper from '../components/ProgressStepper';

/**
 * Report page: show all scores, button to generate final result, display final_risk and explanations.
 */
export default function Report() {
  const {
    userInfo,
    handwritingScore,
    speechScore,
    eyeScore,
    cognitiveScore,
    finalResult,
    setFinalResult,
  } = useAssessment();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerateFinal = async () => {
    setLoading(true);
    setError('');
    try {
      const scores = {
        handwriting: handwritingScore,
        speech: speechScore,
        eye: eyeScore,
        cognitive: cognitiveScore,
      };
      const data = await predictFinal(scores);
      setFinalResult(data);
    } catch (err) {
      setError(err.message || 'Failed to generate result. Is the backend running at http://localhost:8000?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <ProgressStepper currentStep="report" />
      <h2>Assessment report</h2>
      {userInfo.name && (
        <p className="text-muted">
          <strong>Participant:</strong> {userInfo.name}, age {userInfo.age}
        </p>
      )}
      <ScoreCard label="Handwriting risk score" value={handwritingScore} />
      <ScoreCard label="Speech risk score" value={speechScore} />
      <ScoreCard label="Eye tracking risk score" value={eyeScore} />
      <ScoreCard label="Cognitive risk score" value={cognitiveScore} />
      <div className="mt-2 actions-row">
        <button type="button" className="btn-primary" onClick={handleGenerateFinal} disabled={loading}>
          Generate Final Result
        </button>
      </div>
      {loading && <p className="loading">Loading...</p>}
      {error && <p className="error-msg">{error}</p>}
      {finalResult && (
        <div className="report-final">
          <h3>Final result</h3>
          <p>
            <strong>Final risk:</strong>{' '}
            {finalResult.final_risk != null ? finalResult.final_risk : '—'}
          </p>
          {finalResult.explanations && (
            <div className="report-explanations">
              <strong>Explanations</strong>
              <ul>
                {Array.isArray(finalResult.explanations)
                  ? finalResult.explanations.map((exp, i) => <li key={i}>{exp}</li>)
                  : <li>{String(finalResult.explanations)}</li>}
              </ul>
            </div>
          )}
        </div>
      )}
      <div className="mt-2 actions-row">
        <Link to="/cognitive">
          <button type="button" className="btn-secondary">Back</button>
        </Link>
        <Link to="/">
          <button type="button" className="btn-secondary">Home</button>
        </Link>
      </div>
    </div>
  );
}
