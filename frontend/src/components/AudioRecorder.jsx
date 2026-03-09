/**
 * Simple audio recording using MediaRecorder API.
 * Returns blob via onRecordingComplete(blob).
 */
import { useState, useRef } from 'react';

export default function AudioRecorder({ onRecordingComplete }) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        onRecordingComplete(blob);
      };

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone access failed:', err);
      alert('Could not access microphone. Please allow microphone permission.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div>
      {!isRecording ? (
        <button type="button" className="btn-primary" onClick={startRecording}>
          Start Recording
        </button>
      ) : (
        <button type="button" className="btn-secondary" onClick={stopRecording} style={{ borderColor: '#dc2626', color: '#dc2626' }}>
          Stop Recording
        </button>
      )}
    </div>
  );
}
