import { useState } from 'react';
import './TimeEntryReview.css';

interface ProcessedEntry {
  date: string;
  minutes: number;
  task_id?: string;
  project_id?: string;
  activity_name?: string;
  notes: string;
  billable: boolean;
  category_id?: string;
  confidence: number;
  project_name?: string;
  task_name?: string;
  category_name?: string;
  warnings: string[];
}

interface TimeEntryReviewProps {
  entries: ProcessedEntry[];
  totalMinutes: number;
  onConfirm: (entries: ProcessedEntry[]) => void;
  onCancel: () => void;
  transcription: string;
}

const TimeEntryReview: React.FC<TimeEntryReviewProps> = ({
  entries,
  totalMinutes: _totalMinutes,  // Prefixed with _ to indicate intentionally unused
  onConfirm,
  onCancel,
  transcription,
}) => {
  const [editedEntries, setEditedEntries] = useState<ProcessedEntry[]>(entries);
  const [showTranscription, setShowTranscription] = useState(false);

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${mins}m`;
    if (mins === 0) return `${hours}h`;
    return `${hours}h ${mins}m`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  };

  const handleToggleBillable = (index: number) => {
    const updated = [...editedEntries];
    updated[index].billable = !updated[index].billable;
    setEditedEntries(updated);
  };

  const handleRemoveEntry = (index: number) => {
    const updated = editedEntries.filter((_, i) => i !== index);
    setEditedEntries(updated);
  };

  const handleUpdateNotes = (index: number, notes: string) => {
    const updated = [...editedEntries];
    updated[index].notes = notes;
    setEditedEntries(updated);
  };

  const handleUpdateMinutes = (index: number, minutes: number) => {
    if (minutes > 0 && minutes <= 1440) {
      const updated = [...editedEntries];
      updated[index].minutes = minutes;
      setEditedEntries(updated);
    }
  };

  const getTotalMinutes = () => {
    return editedEntries.reduce((sum, entry) => sum + entry.minutes, 0);
  };

  return (
    <div className="time-entry-review-container">
      <div className="time-entry-review">
        <h3>Review Time Entries</h3>
        
        <div className="review-summary">
          <p>We&apos;ve processed your recording into {editedEntries.length} time entries.</p>
          <p className="total-time">Total time: {formatDuration(getTotalMinutes())}</p>
        </div>

        <button 
          className="show-transcription-button"
          onClick={() => setShowTranscription(!showTranscription)}
        >
          {showTranscription ? 'Hide' : 'Show'} Original Transcription
        </button>

        {showTranscription && (
          <div className="transcription-box">
            <p>{transcription}</p>
          </div>
        )}

        <div className="entries-list">
          {editedEntries.map((entry, index) => (
            <div key={index} className="review-entry">
              <div className="entry-header">
                <div className="entry-main-info">
                  <div className="entry-time">
                    <input
                      type="number"
                      min="1"
                      max="1440"
                      value={Math.floor(entry.minutes / 60)}
                      onChange={(e) => {
                        const hours = parseInt(e.target.value) || 0;
                        const mins = entry.minutes % 60;
                        handleUpdateMinutes(index, hours * 60 + mins);
                      }}
                      className="time-input"
                    />
                    <span>h</span>
                    <input
                      type="number"
                      min="0"
                      max="59"
                      value={entry.minutes % 60}
                      onChange={(e) => {
                        const hours = Math.floor(entry.minutes / 60);
                        const mins = parseInt(e.target.value) || 0;
                        handleUpdateMinutes(index, hours * 60 + mins);
                      }}
                      className="time-input"
                    />
                    <span>m</span>
                  </div>
                  <div className={`confidence-badge ${getConfidenceColor(entry.confidence)}`}>
                    {getConfidenceLabel(entry.confidence)} Confidence
                    <span className="confidence-value">({Math.round(entry.confidence * 100)}%)</span>
                  </div>
                </div>
                <button 
                  className="remove-entry-button"
                  onClick={() => handleRemoveEntry(index)}
                  title="Remove this entry"
                >
                  ×
                </button>
              </div>

              <div className="entry-details">
                {entry.project_name ? (
                  <div className="detail-row">
                    <span className="detail-label">Project:</span>
                    <span className="detail-value">{entry.project_name}</span>
                  </div>
                ) : entry.activity_name ? (
                  <div className="detail-row">
                    <span className="detail-label">Activity:</span>
                    <span className="detail-value">{entry.activity_name}</span>
                  </div>
                ) : (
                  <div className="detail-row warning">
                    <span className="warning-icon">⚠️</span>
                    <span>No project or activity specified</span>
                  </div>
                )}

                {entry.task_name && (
                  <div className="detail-row">
                    <span className="detail-label">Task:</span>
                    <span className="detail-value">{entry.task_name}</span>
                  </div>
                )}

                {entry.category_name && (
                  <div className="detail-row">
                    <span className="detail-label">Category:</span>
                    <span className="detail-value">{entry.category_name}</span>
                  </div>
                )}

                <div className="detail-row">
                  <span className="detail-label">Notes:</span>
                  <textarea
                    value={entry.notes}
                    onChange={(e) => handleUpdateNotes(index, e.target.value)}
                    className="notes-input"
                    placeholder="Add notes..."
                    rows={2}
                  />
                </div>

                <div className="entry-badges">
                  <button
                    className={`billable-toggle ${entry.billable ? 'billable' : 'non-billable'}`}
                    onClick={() => handleToggleBillable(index)}
                  >
                    {entry.billable ? 'Billable' : 'Non-Billable'}
                  </button>
                </div>

                {entry.warnings.length > 0 && (
                  <div className="warnings-list">
                    {entry.warnings.map((warning, wIndex) => (
                      <div key={wIndex} className="warning-item">
                        <span className="warning-icon">⚠️</span>
                        <span>{warning}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {editedEntries.length === 0 && (
          <div className="no-entries">
            <p>No time entries to submit.</p>
          </div>
        )}

        <div className="review-actions">
          <button onClick={onCancel} className="cancel-button">
            Cancel
          </button>
          <button 
            onClick={() => onConfirm(editedEntries)} 
            className="confirm-button"
            disabled={editedEntries.length === 0}
          >
            Submit {editedEntries.length} {editedEntries.length === 1 ? 'Entry' : 'Entries'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TimeEntryReview;