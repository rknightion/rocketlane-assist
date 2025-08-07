import { useState, useRef, useEffect } from 'react';
import './AudioRecorder.css';

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  onCancel: () => void;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ onRecordingComplete, onCancel }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Request microphone permission and get available devices
    const initializeAudio = async () => {
      try {
        // Request permission first
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop()); // Stop the test stream
        
        setPermissionGranted(true);
        
        // Get available audio devices
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(device => device.kind === 'audioinput');
        setAudioDevices(audioInputs);
        
        // Set default device
        if (audioInputs.length > 0 && !selectedDeviceId) {
          setSelectedDeviceId(audioInputs[0].deviceId);
        }
      } catch (err) {
        console.error('Failed to get microphone permission:', err);
        setError('Microphone permission denied. Please allow microphone access and try again.');
      }
    };
    
    initializeAudio();
    
    return () => {
      // Cleanup
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const startRecording = async () => {
    try {
      setError(null);
      audioChunksRef.current = [];
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          deviceId: selectedDeviceId ? { exact: selectedDeviceId } : undefined,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
      });

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        onRecordingComplete(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Failed to start recording:', err);
      setError('Failed to start recording. Please check your microphone and try again.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (error) {
    return (
      <div className="audio-recorder-container">
        <div className="audio-recorder-error">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button onClick={onCancel} className="cancel-button">Close</button>
        </div>
      </div>
    );
  }

  if (!permissionGranted) {
    return (
      <div className="audio-recorder-container">
        <div className="audio-recorder-permission">
          <span className="permission-icon">🎤</span>
          <p>Requesting microphone permission...</p>
          <p className="permission-hint">Please allow microphone access when prompted.</p>
          <button onClick={onCancel} className="cancel-button">Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div className="audio-recorder-container">
      <div className="audio-recorder">
        <h3>Record Your Day</h3>
        
        <div className="instructions">
          <p>Explain what you worked on today. Your recording will be transcribed and processed to create time entries.</p>
          <p className="hint">Example: &quot;I spent 2 hours on the Roche project working on TSM tasks, then 1 hour on internal admin work which is non-billable.&quot;</p>
        </div>

        {audioDevices.length > 1 && (
          <div className="microphone-selector">
            <label>Select Microphone:</label>
            <select 
              value={selectedDeviceId} 
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              disabled={isRecording}
            >
              {audioDevices.map(device => (
                <option key={device.deviceId} value={device.deviceId}>
                  {device.label || `Microphone ${device.deviceId.slice(0, 5)}...`}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="recording-controls">
          {!isRecording ? (
            <button 
              className="record-button"
              onClick={startRecording}
              title="Start Recording"
            >
              <span className="record-icon">🔴</span>
              Start Recording
            </button>
          ) : (
            <>
              <div className="recording-status">
                <span className="recording-indicator"></span>
                <span className="recording-time">{formatTime(recordingTime)}</span>
                <span className="recording-label">Recording...</span>
              </div>
              <button 
                className="stop-button"
                onClick={stopRecording}
                title="Stop Recording"
              >
                <span className="stop-icon">⏹</span>
                Stop Recording
              </button>
            </>
          )}
        </div>

        {!isRecording && (
          <button onClick={onCancel} className="cancel-button">
            Cancel
          </button>
        )}
      </div>
    </div>
  );
};

export default AudioRecorder;