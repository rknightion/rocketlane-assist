import { useState, useEffect } from 'react';
import { timesheetsApi } from '../services/api';
import './Timesheets.css';

interface TimeEntry {
  id?: string;
  date: string;
  minutes: number;
  task_id?: string;
  project_id?: string;
  activity_name?: string;
  notes: string;
  billable: boolean;
  category_id?: string;
  task?: any;
  project?: any;
}

interface Project {
  projectId: string;
  projectName: string;
  status?: any;
  customer?: any;
}

interface Task {
  taskId: string;
  taskName: string;
  project?: any;
  status?: any;
  priority?: any;
}

interface Category {
  id: string;
  name: string;
}

const Timesheets = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedWeek, setSelectedWeek] = useState(getWeekDates(new Date()));
  const [entries, setEntries] = useState<TimeEntry[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showAddEntry, setShowAddEntry] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [newEntry, setNewEntry] = useState<TimeEntry>({
    date: '',
    minutes: 0,
    notes: '',
    billable: true,
  });
  const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, [selectedWeek]);

  useEffect(() => {
    // Filter tasks when project is selected
    if (newEntry.project_id) {
      const projectTasks = tasks.filter(task => 
        task.project?.projectId === newEntry.project_id
      );
      setFilteredTasks(projectTasks);
    } else {
      setFilteredTasks(tasks);
    }
  }, [newEntry.project_id, tasks]);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const [fetchedProjects, fetchedTasks, fetchedCategories, fetchedEntries, fetchedSummary] = await Promise.all([
        timesheetsApi.getProjects(),
        timesheetsApi.getTasks(),
        timesheetsApi.getCategories(),
        timesheetsApi.getEntries(selectedWeek.start, selectedWeek.end),
        timesheetsApi.getSummary(selectedWeek.start, selectedWeek.end),
      ]);

      setProjects(fetchedProjects);
      setTasks(fetchedTasks);
      setCategories(fetchedCategories);
      setEntries(fetchedEntries);
      setSummary(fetchedSummary);
    } catch (err) {
      console.error('Failed to load timesheet data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  function getWeekDates(date: Date) {
    const startOfWeek = new Date(date);
    startOfWeek.setDate(date.getDate() - date.getDay());
    
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    
    return {
      start: startOfWeek.toISOString().split('T')[0],
      end: endOfWeek.toISOString().split('T')[0],
    };
  }

  function getWeekDays() {
    const days = [];
    const start = new Date(selectedWeek.start);
    
    for (let i = 0; i < 7; i++) {
      const day = new Date(start);
      day.setDate(start.getDate() + i);
      days.push({
        date: day.toISOString().split('T')[0],
        dayName: day.toLocaleDateString('en-US', { weekday: 'short' }),
        dayNumber: day.getDate(),
        isToday: day.toDateString() === new Date().toDateString(),
      });
    }
    
    return days;
  }

  function navigateWeek(direction: 'prev' | 'next') {
    const current = new Date(selectedWeek.start);
    current.setDate(current.getDate() + (direction === 'next' ? 7 : -7));
    setSelectedWeek(getWeekDates(current));
  }

  function goToCurrentWeek() {
    setSelectedWeek(getWeekDates(new Date()));
  }

  function getEntriesForDate(date: string) {
    return entries.filter(entry => 
      (entry.date === date) || (entry as any).entryDate === date
    );
  }

  function getTotalMinutesForDate(date: string) {
    const dateEntries = getEntriesForDate(date);
    return dateEntries.reduce((sum, entry) => 
      sum + (entry.minutes || (entry as any).durationInMinutes || 0), 0
    );
  }

  function formatDuration(minutes: number) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours === 0) return `${mins}m`;
    if (mins === 0) return `${hours}h`;
    return `${hours}h ${mins}m`;
  }

  function openAddEntry(date: string) {
    setSelectedDate(date);
    setNewEntry({
      date,
      minutes: 0,
      notes: '',
      billable: true,
    });
    setShowAddEntry(true);
  }

  async function handleAddEntry() {
    try {
      // Convert hours and minutes to total minutes
      const hours = Math.floor(newEntry.minutes / 60);
      const minutes = newEntry.minutes % 60;
      const totalMinutes = (hours * 60) + minutes;
      
      if (totalMinutes <= 0) {
        alert('Please enter a valid duration');
        return;
      }
      
      // Validation: Either both project AND task, or activity name
      if (newEntry.project_id) {
        if (!newEntry.task_id) {
          alert('Please select a task for the selected project');
          return;
        }
      } else if (!newEntry.activity_name) {
        alert('Please either select a project and task, or enter an activity name');
        return;
      }
      
      await timesheetsApi.createEntry({
        ...newEntry,
        minutes: totalMinutes,
      });
      
      // Reload data
      await loadData();
      setShowAddEntry(false);
    } catch (err) {
      console.error('Failed to create time entry:', err);
      alert('Failed to create time entry. Please try again.');
    }
  }

  if (loading && !entries.length) {
    return (
      <div className="timesheets-page">
        <div className="loading">Loading timesheet data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="timesheets-page">
        <div className="error">
          <h2>Error Loading Timesheets</h2>
          <p>{error}</p>
          <button onClick={loadData}>Retry</button>
        </div>
      </div>
    );
  }

  const weekDays = getWeekDays();
  const weekStart = new Date(selectedWeek.start);
  const weekEnd = new Date(selectedWeek.end);
  const weekDisplay = `${weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;

  return (
    <div className="timesheets-page">
      <div className="timesheets-header">
        <h1>Timesheets</h1>
        <div className="week-navigation">
          <button onClick={() => navigateWeek('prev')} className="nav-button">
            ← Previous Week
          </button>
          <div className="week-display">
            <span>{weekDisplay}</span>
            {selectedWeek.start !== getWeekDates(new Date()).start && (
              <button onClick={goToCurrentWeek} className="today-button">
                Today
              </button>
            )}
          </div>
          <button onClick={() => navigateWeek('next')} className="nav-button">
            Next Week →
          </button>
        </div>
      </div>

      {summary && (
        <div className="week-summary">
          <div className="summary-card">
            <div className="summary-label">Total Hours</div>
            <div className="summary-value">{summary.totalHours}h</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Entries</div>
            <div className="summary-value">{summary.entryCount}</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Projects</div>
            <div className="summary-value">{summary.byProject?.length || 0}</div>
          </div>
        </div>
      )}

      <div className="timesheet-grid">
        {weekDays.map(day => {
          const dayEntries = getEntriesForDate(day.date);
          const totalMinutes = getTotalMinutesForDate(day.date);
          
          return (
            <div key={day.date} className={`day-column ${day.isToday ? 'today' : ''}`}>
              <div className="day-header">
                <div className="day-name">{day.dayName}</div>
                <div className="day-number">{day.dayNumber}</div>
                {totalMinutes > 0 && (
                  <div className="day-total">{formatDuration(totalMinutes)}</div>
                )}
              </div>
              
              <div className="day-entries">
                {dayEntries.map((entry, index) => (
                  <div key={entry.id || index} className="time-entry">
                    <div className="entry-project">
                      {entry.task?.project?.projectName || 
                       entry.project?.projectName || 
                       (entry as any).project?.projectName ||
                       'Ad-hoc Activity'}
                    </div>
                    <div className="entry-task">
                      {entry.task?.taskName || 
                       (entry as any).task?.taskName ||
                       entry.activity_name || 
                       (entry as any).activityName ||
                       'General Work'}
                    </div>
                    {(entry.notes || (entry as any).notes) && (
                      <div className="entry-notes">
                        {entry.notes || (entry as any).notes}
                      </div>
                    )}
                    <div className="entry-duration">
                      {formatDuration(entry.minutes || (entry as any).durationInMinutes || 0)}
                    </div>
                  </div>
                ))}
              </div>
              
              <button 
                className="add-entry-button"
                onClick={() => openAddEntry(day.date)}
              >
                + Add Entry
              </button>
            </div>
          );
        })}
      </div>

      {showAddEntry && (
        <div className="modal-overlay" onClick={() => setShowAddEntry(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Add Time Entry</h2>
            <div className="entry-date">{new Date(selectedDate).toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}</div>
            
            <div className="form-group">
              <label>Project</label>
              <select
                value={newEntry.project_id || ''}
                onChange={e => setNewEntry({ ...newEntry, project_id: e.target.value, task_id: undefined })}
              >
                <option value="">Select a project...</option>
                {projects.map(project => (
                  <option key={project.projectId} value={project.projectId}>
                    {project.projectName}
                  </option>
                ))}
              </select>
            </div>
            
            {newEntry.project_id && (
              <div className="form-group">
                <label>Task (Required)</label>
                <select
                  value={newEntry.task_id || ''}
                  onChange={e => setNewEntry({ ...newEntry, task_id: e.target.value })}
                  required
                >
                  <option value="">Select a task...</option>
                  {filteredTasks.map(task => (
                    <option key={task.taskId} value={task.taskId}>
                      {task.taskName}
                    </option>
                  ))}
                </select>
              </div>
            )}
            
            {!newEntry.project_id && (
              <div className="form-group">
                <label>Activity Name</label>
                <input
                  type="text"
                  value={newEntry.activity_name || ''}
                  onChange={e => setNewEntry({ ...newEntry, activity_name: e.target.value })}
                  placeholder="Enter activity description..."
                />
              </div>
            )}
            
            <div className="form-group">
              <label>Duration</label>
              <div className="duration-input">
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={Math.floor(newEntry.minutes / 60)}
                  onChange={e => {
                    const hours = parseInt(e.target.value) || 0;
                    const mins = newEntry.minutes % 60;
                    setNewEntry({ ...newEntry, minutes: (hours * 60) + mins });
                  }}
                  placeholder="0"
                />
                <span>hours</span>
                <input
                  type="number"
                  min="0"
                  max="59"
                  value={newEntry.minutes % 60}
                  onChange={e => {
                    const hours = Math.floor(newEntry.minutes / 60);
                    const mins = parseInt(e.target.value) || 0;
                    setNewEntry({ ...newEntry, minutes: (hours * 60) + mins });
                  }}
                  placeholder="0"
                />
                <span>minutes</span>
              </div>
            </div>
            
            {categories.length > 0 && (
              <div className="form-group">
                <label>Category</label>
                <select
                  value={newEntry.category_id || ''}
                  onChange={e => setNewEntry({ ...newEntry, category_id: e.target.value })}
                >
                  <option value="">Select a category...</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            
            <div className="form-group">
              <label>Notes</label>
              <textarea
                value={newEntry.notes}
                onChange={e => setNewEntry({ ...newEntry, notes: e.target.value })}
                placeholder="What did you work on?"
                rows={3}
              />
            </div>
            
            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={newEntry.billable}
                  onChange={e => setNewEntry({ ...newEntry, billable: e.target.checked })}
                />
                <span>Billable</span>
              </label>
            </div>
            
            <div className="modal-actions">
              <button onClick={() => setShowAddEntry(false)} className="cancel-button">
                Cancel
              </button>
              <button onClick={handleAddEntry} className="save-button">
                Add Entry
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Timesheets;