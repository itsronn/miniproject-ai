import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import UserInfo from './pages/UserInfo';
import HandwritingTest from './pages/HandwritingTest';
import SpeechTest from './pages/SpeechTest';
import EyeTrackingTest from './pages/EyeTrackingTest';
import CognitiveTest from './pages/CognitiveTest';
import Report from './pages/Report';

/**
 * App - Route definitions. AssessmentProvider wraps from main.jsx.
 */
function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/user" element={<UserInfo />} />
      <Route path="/handwriting" element={<HandwritingTest />} />
      <Route path="/speech" element={<SpeechTest />} />
      <Route path="/eye" element={<EyeTrackingTest />} />
      <Route path="/cognitive" element={<CognitiveTest />} />
      <Route path="/report" element={<Report />} />
    </Routes>
  );
}

export default App;
