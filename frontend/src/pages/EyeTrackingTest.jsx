import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import ProgressStepper from '../components/ProgressStepper';

// TODO: Future integration with MediaPipe or similar for eye-tracking.
// This page is a placeholder; no eye-tracking logic is implemented.

/**
 * Eye tracking placeholder. Skip / Continue only.
 */
export default function EyeTrackingTest() {
  const navigate = useNavigate();

  return (
    <div className="card">
      <ProgressStepper currentStep="eyetracking" />
      <h2>Eye tracking (coming soon)</h2>
      <p className="text-muted">
        This step will later use gaze tracking to understand how children scan and follow visual information.
        For now, it&apos;s a placeholder and doesn&apos;t affect the final result.
      </p>
      <div className="mt-2 actions-row">
        <button type="button" className="btn-primary" onClick={() => navigate('/cognitive')}>
          Continue
        </button>
        <Link to="/speech">
          <button type="button" className="btn-secondary">Back</button>
        </Link>
      </div>
    </div>
  );
}
