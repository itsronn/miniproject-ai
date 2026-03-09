import { createContext, useContext, useState } from 'react';

/**
 * AssessmentContext - Global state for the screening flow.
 * Holds user info and all module scores. Simple implementation.
 */
const AssessmentContext = createContext(null);

export function AssessmentProvider({ children }) {
  const [userInfo, setUserInfo] = useState({});
  const [handwritingScore, setHandwritingScore] = useState(null);
  const [speechScore, setSpeechScore] = useState(null);
  const [eyeScore, setEyeScore] = useState(null);
  const [cognitiveScore, setCognitiveScore] = useState(null);
  const [finalResult, setFinalResult] = useState(null);

  const value = {
    userInfo,
    setUserInfo,
    handwritingScore,
    setHandwritingScore,
    speechScore,
    setSpeechScore,
    eyeScore,
    setEyeScore,
    cognitiveScore,
    setCognitiveScore,
    finalResult,
    setFinalResult,
  };

  return (
    <AssessmentContext.Provider value={value}>
      {children}
    </AssessmentContext.Provider>
  );
}

export function useAssessment() {
  const ctx = useContext(AssessmentContext);
  if (!ctx) {
    throw new Error('useAssessment must be used within AssessmentProvider');
  }
  return ctx;
}
