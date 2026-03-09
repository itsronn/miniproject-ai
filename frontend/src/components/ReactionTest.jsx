/**
 * Simple reaction time test: wait for random delay, then measure click time.
 * Calls onComplete(metrics) with { reactionTimes: number[], averageMs: number }.
 */
import { useState, useRef } from 'react';

const NUM_TRIALS = 3;
const MIN_DELAY_MS = 1000;
const MAX_DELAY_MS = 3000;

export default function ReactionTest({ onComplete }) {
  const [phase, setPhase] = useState('ready'); // 'ready' | 'wait' | 'click' | 'done'
  const [trial, setTrial] = useState(0);
  const [reactionTimes, setReactionTimes] = useState([]);
  const startTimeRef = useRef(null);

  const runTrial = () => {
    if (trial >= NUM_TRIALS) {
      const times = [...reactionTimes];
      const avg = times.length ? times.reduce((a, b) => a + b, 0) / times.length : 0;
      onComplete({ reactionTimes: times, averageMs: Math.round(avg) });
      setPhase('done');
      return;
    }
    setPhase('wait');
    const delay = MIN_DELAY_MS + Math.random() * (MAX_DELAY_MS - MIN_DELAY_MS);
    setTimeout(() => {
      setPhase('click');
      startTimeRef.current = Date.now();
    }, delay);
  };

  const handleClick = () => {
    if (phase !== 'click') return;
    const elapsed = Date.now() - startTimeRef.current;
    const next = [...reactionTimes, elapsed];
    setReactionTimes(next);
    setTrial((t) => t + 1);
    setPhase('ready');
    if (next.length >= NUM_TRIALS) {
      const avg = next.reduce((a, b) => a + b, 0) / next.length;
      onComplete({ reactionTimes: next, averageMs: Math.round(avg) });
      setPhase('done');
    } else {
      setTimeout(runTrial, 500);
    }
  };

  return (
    <div>
      {phase === 'ready' && trial < NUM_TRIALS && (
        <>
          <p>Trial {trial + 1} of {NUM_TRIALS}. Click the button when it turns green.</p>
          <button type="button" className="btn-primary" onClick={runTrial}>
            Click when ready
          </button>
        </>
      )}
      {phase === 'wait' && <p>Wait for the green light...</p>}
      {phase === 'click' && (
        <button
          type="button"
          onClick={handleClick}
          style={{ background: '#22c55e', padding: '1.5rem 2rem', fontSize: '1.2rem' }}
        >
          CLICK NOW
        </button>
      )}
      {phase === 'done' && (
        <p className="loading">Reaction test complete. Average: {reactionTimes.length ? (reactionTimes.reduce((a, b) => a + b, 0) / reactionTimes.length).toFixed(0) : 0} ms</p>
      )}
    </div>
  );
}
