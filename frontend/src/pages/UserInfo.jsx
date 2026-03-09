import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAssessment } from '../context/AssessmentContext';
import ProgressStepper from '../components/ProgressStepper';

/**
 * User info form. Name, age, consent. Save to context. Continue disabled if invalid.
 */
export default function UserInfo() {
  const { userInfo, setUserInfo } = useAssessment();
  const navigate = useNavigate();
  const [name, setName] = useState(userInfo.name ?? '');
  const [age, setAge] = useState(userInfo.age ?? '');
  const [consent, setConsent] = useState(userInfo.consent ?? false);

  const isValid = name.trim() && age.trim() && Number(age) > 0 && Number(age) < 120 && consent;

  const handleSave = () => {
    setUserInfo({ name: name.trim(), age: age.trim(), consent });
    navigate('/handwriting');
  };

  return (
    <div className="card">
      <ProgressStepper currentStep="userinfo" />
      <h2>Your information</h2>
      <p className="text-muted">
        We only ask for a few details to personalise the assessment. Data stays local to this research prototype.
      </p>
      <label>Name</label>
      <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" />
      <label>Age</label>
      <input type="number" value={age} onChange={(e) => setAge(e.target.value)} placeholder="Age" min={1} max={119} />
      <label className="consent-row">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        I consent to this assessment and data use for screening purposes.
      </label>
      <div className="actions-row">
        <button type="button" className="btn-primary" onClick={handleSave} disabled={!isValid}>
          Continue
        </button>
        <Link to="/">
          <button type="button" className="btn-secondary">Back</button>
        </Link>
      </div>
    </div>
  );
}
