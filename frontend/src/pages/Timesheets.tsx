import { useState, useEffect } from 'react';
import { timesheetsApi } from '../services/api';
import './Timesheets.css';

interface TimeEntry {
  id?: string;
  timeEntryId?: string;
  date: string;
  entryDate?: string;
  minutes: number;
  durationInMinutes?: number;
  task_id?: string;
  project_id?: string;
  activity_name?: string;
  activityName?: string;
  notes: string;
  billable: boolean;
  category_id?: string;
  task?: any;
  project?: any;
  category?: any;
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
  const [editingEntry, setEditingEntry] = useState<TimeEntry | null>(null);
  const [newEntry, setNewEntry] = useState<TimeEntry>({
    date: '',
    minutes: 0,
    notes: '',
    billable: true,
  });
  const [filteredTasks, setFilteredTasks] = useState<Task[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [includeWeekends, setIncludeWeekends] = useState(false);
  const [draggedEntry, setDraggedEntry] = useState<TimeEntry | null>(null);
  const [dragOverDate, setDragOverDate] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [selectedWeek]);

  useEffect(() => {
    // Filter tasks when project is selected
    if (newEntry.project_id) {
      const projectTasks = tasks.filter(task => {
        // Compare as strings to handle both string and number IDs
        const taskProjectId = String(task.project?.projectId || '');
        const selectedProjectId = String(newEntry.project_id);
        return taskProjectId === selectedProjectId;
      });
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

  async function refreshEntries() {
    try {
      await timesheetsApi.refreshEntries(selectedWeek.start, selectedWeek.end);
      await loadData();
    } catch (err) {
      console.error('Failed to refresh entries:', err);
      // Still try to load data even if refresh fails
      try {
        await loadData();
      } catch (loadErr) {
        console.error('Failed to load data after refresh error:', loadErr);
      }
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
      const dayOfWeek = day.getDay();
      
      // Skip weekends if not included
      if (!includeWeekends && (dayOfWeek === 0 || dayOfWeek === 6)) {
        continue;
      }
      
      days.push({
        date: day.toISOString().split('T')[0],
        dayName: day.toLocaleDateString('en-US', { weekday: 'short' }),
        dayNumber: day.getDate(),
        monthName: day.toLocaleDateString('en-US', { month: 'short' }),
        isToday: day.toDateString() === new Date().toDateString(),
        isWeekend: dayOfWeek === 0 || dayOfWeek === 6,
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
      (entry.date === date) || (entry.entryDate === date)
    );
  }

  function getTotalMinutesForDate(date: string) {
    const dateEntries = getEntriesForDate(date);
    return dateEntries.reduce((sum, entry) => 
      sum + (entry.minutes || entry.durationInMinutes || 0), 0
    );
  }

  function getBillableMinutesForDate(date: string) {
    const dateEntries = getEntriesForDate(date);
    return dateEntries.reduce((sum, entry) => {
      if (entry.billable !== false) {
        return sum + (entry.minutes || entry.durationInMinutes || 0);
      }
      return sum;
    }, 0);
  }

  function getNonBillableMinutesForDate(date: string) {
    const dateEntries = getEntriesForDate(date);
    return dateEntries.reduce((sum, entry) => {
      if (entry.billable === false) {
        return sum + (entry.minutes || entry.durationInMinutes || 0);
      }
      return sum;
    }, 0);
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
    setEditingEntry(null);
    setShowAddEntry(true);
  }

  function openEditEntry(entry: TimeEntry) {
    const entryId = entry.id || entry.timeEntryId;
    const entryDate = entry.date || entry.entryDate || '';
    const entryMinutes = entry.minutes || entry.durationInMinutes || 0;
    const entryNotes = entry.notes || '';
    const entryActivityName = entry.activity_name || entry.activityName || '';
    
    setSelectedDate(entryDate);
    setNewEntry({
      date: entryDate,
      minutes: entryMinutes,
      task_id: entry.task?.taskId ? String(entry.task.taskId) : undefined,
      project_id: entry.project?.projectId ? String(entry.project.projectId) : undefined,
      activity_name: entryActivityName,
      notes: entryNotes,
      billable: entry.billable !== undefined ? entry.billable : true,
      category_id: entry.category?.categoryId ? String(entry.category.categoryId) : undefined,
    });
    setEditingEntry({ ...entry, id: entryId });
    setShowAddEntry(true);
  }

  function duplicateEntry(entry: TimeEntry) {
    const entryDate = entry.date || entry.entryDate || '';
    const entryMinutes = entry.minutes || entry.durationInMinutes || 0;
    const entryNotes = entry.notes || '';
    const entryActivityName = entry.activity_name || entry.activityName || '';
    
    setSelectedDate(entryDate);
    setNewEntry({
      date: entryDate,
      minutes: entryMinutes,
      task_id: entry.task?.taskId ? String(entry.task.taskId) : undefined,
      project_id: entry.project?.projectId ? String(entry.project.projectId) : undefined,
      activity_name: entryActivityName,
      notes: entryNotes,
      billable: entry.billable !== undefined ? entry.billable : true,
      category_id: entry.category?.categoryId ? String(entry.category.categoryId) : undefined,
    });
    setEditingEntry(null);
    setShowAddEntry(true);
  }

  async function handleSaveEntry() {
    try {
      // Convert hours and minutes to total minutes
      const totalMinutes = newEntry.minutes;
      
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
      
      const entryData = {
        ...newEntry,
        minutes: totalMinutes,
      };
      
      if (editingEntry) {
        // Update existing entry
        const entryId = editingEntry.id || editingEntry.timeEntryId;
        await timesheetsApi.updateEntry(entryId!, entryData, selectedWeek.start, selectedWeek.end);
      } else {
        // Create new entry
        await timesheetsApi.createEntry(entryData, selectedWeek.start, selectedWeek.end);
      }
      
      // Add small delay to ensure Rocketlane API has processed the changes
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Reload data
      await loadData();
      setShowAddEntry(false);
    } catch (err) {
      console.error('Failed to save time entry:', err);
      alert('Failed to save time entry. Please try again.');
    }
  }

  async function handleDeleteEntry(entry: TimeEntry) {
    if (!confirm('Are you sure you want to delete this time entry?')) {
      return;
    }
    
    try {
      const entryId = entry.id || entry.timeEntryId;
      await timesheetsApi.deleteEntry(entryId!, selectedWeek.start, selectedWeek.end);
      await loadData();
    } catch (err) {
      console.error('Failed to delete time entry:', err);
      alert('Failed to delete time entry. Please try again.');
    }
  }

  async function handleDeleteAllEntries(date: string) {
    const dayEntries = getEntriesForDate(date);
    
    if (dayEntries.length === 0) {
      return;
    }
    
    const dayName = new Date(date).toLocaleDateString('en-US', { 
      weekday: 'long', 
      month: 'long', 
      day: 'numeric' 
    });
    
    if (!confirm(`Are you sure you want to delete all ${dayEntries.length} time entries for ${dayName}?\n\nThis action cannot be undone.`)) {
      return;
    }
    
    try {
      // Delete all entries for this day
      const deletePromises = dayEntries.map(entry => {
        const entryId = entry.id || entry.timeEntryId;
        return timesheetsApi.deleteEntry(entryId!, selectedWeek.start, selectedWeek.end);
      });
      
      await Promise.all(deletePromises);
      
      // Refresh the data after deleting
      await loadData();
    } catch (err) {
      console.error('Failed to delete entries:', err);
      alert('Failed to delete some entries. Please try again.');
    }
  }

  function handleDragStart(e: React.DragEvent, entry: TimeEntry) {
    setDraggedEntry(entry);
    e.dataTransfer.effectAllowed = 'copyMove';
  }

  function handleDragOver(e: React.DragEvent, date: string) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverDate(date);
  }

  function handleDragLeave() {
    setDragOverDate(null);
  }

  async function handleDrop(e: React.DragEvent, targetDate: string) {
    e.preventDefault();
    setDragOverDate(null);
    
    if (!draggedEntry) return;
    
    const sourceDate = draggedEntry.date || draggedEntry.entryDate;
    if (sourceDate === targetDate) {
      setDraggedEntry(null);
      return;
    }
    
    // Show dialog to ask user for copy or move
    const action = await showCopyMoveDialog();
    
    if (action === 'copy') {
      // Copy entry to new date - use same format as manual entry creation
      const entryData: TimeEntry = {
        date: targetDate,
        minutes: draggedEntry.minutes || draggedEntry.durationInMinutes || 0,
        task_id: draggedEntry.task?.taskId ? String(draggedEntry.task.taskId) : undefined,
        project_id: draggedEntry.project?.projectId ? String(draggedEntry.project.projectId) : undefined,
        activity_name: draggedEntry.activity_name || draggedEntry.activityName,
        notes: draggedEntry.notes || '',
        billable: draggedEntry.billable !== false,
        category_id: draggedEntry.category?.categoryId ? String(draggedEntry.category.categoryId) : undefined,
      };
      
      try {
        // Remember current entry count for validation
        const initialEntryCount = entries.length;
        
        // Pass date range for proper cache invalidation (like delete does)
        await timesheetsApi.createEntry(entryData, selectedWeek.start, selectedWeek.end);
        
        // Retry loading data until we see the new entry (max 10 attempts)
        let retries = 10;
        let success = false;
        
        while (retries > 0 && !success) {
          // Wait before fetching (fixed 500ms delay)
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Force refresh the cache on the backend
          try {
            await timesheetsApi.refreshEntries(selectedWeek.start, selectedWeek.end);
          } catch (err) {
            console.log('Cache refresh failed, continuing...');
          }
          
          // Reload data
          await loadData();
          
          // Check if the entry count increased (successful copy)
          if (entries.length > initialEntryCount) {
            success = true;
            console.log('Copy successful - new entry detected');
          } else {
            console.log(`Retry ${11 - retries}/10 - waiting for Rocketlane to process entry...`);
            retries--;
          }
        }
        
        if (!success) {
          // Final attempt - one more refresh
          await timesheetsApi.refreshEntries(selectedWeek.start, selectedWeek.end);
          await loadData();
        }
      } catch (err) {
        console.error('Failed to copy entry:', err);
        alert('Failed to copy entry. Please try again.');
      }
    } else if (action === 'move') {
      // Move entry to new date - use same format as manual entry update
      const entryId = draggedEntry.id || draggedEntry.timeEntryId;
      
      const entryData: TimeEntry = {
        date: targetDate,
        minutes: draggedEntry.minutes || draggedEntry.durationInMinutes || 0,
        task_id: draggedEntry.task?.taskId ? String(draggedEntry.task.taskId) : undefined,
        project_id: draggedEntry.project?.projectId ? String(draggedEntry.project.projectId) : undefined,
        activity_name: draggedEntry.activity_name || draggedEntry.activityName,
        notes: draggedEntry.notes || '',
        billable: draggedEntry.billable !== false,
        category_id: draggedEntry.category?.categoryId ? String(draggedEntry.category.categoryId) : undefined,
      };
      
      try {
        // Pass date range for proper cache invalidation (like delete does)
        await timesheetsApi.updateEntry(entryId!, entryData, selectedWeek.start, selectedWeek.end);
        
        // Retry loading data until we see the moved entry (max 10 attempts)
        let retries = 10;
        let success = false;
        
        while (retries > 0 && !success) {
          // Wait before fetching (fixed 500ms delay)
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Force refresh the cache on the backend
          try {
            await timesheetsApi.refreshEntries(selectedWeek.start, selectedWeek.end);
          } catch (err) {
            console.log('Cache refresh failed, continuing...');
          }
          
          // Reload data
          await loadData();
          
          // Check if the entry has moved to the target date
          const targetDateEntries = getEntriesForDate(targetDate);
          const movedEntry = targetDateEntries.find(e => 
            (e.id === entryId || e.timeEntryId === entryId)
          );
          
          if (movedEntry) {
            success = true;
            console.log('Move successful - entry found at target date');
          } else {
            console.log(`Retry ${11 - retries}/10 - waiting for Rocketlane to process move...`);
            retries--;
          }
        }
        
        if (!success) {
          // Final attempt - one more refresh
          await timesheetsApi.refreshEntries(selectedWeek.start, selectedWeek.end);
          await loadData();
        }
      } catch (err) {
        console.error('Failed to move entry:', err);
        alert('Failed to move entry. Please try again.');
      }
    }
    
    setDraggedEntry(null);
  }

  function showCopyMoveDialog(): Promise<'copy' | 'move' | null> {
    return new Promise((resolve) => {
      const modal = document.createElement('div');
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-content copy-move-dialog">
          <h3>Move or Copy Entry?</h3>
          <p>Would you like to move this entry to the new date or create a copy?</p>
          <div class="modal-actions">
            <button class="cancel-button" id="cancel-action">Cancel</button>
            <button class="copy-button" id="copy-action">Copy Entry</button>
            <button class="save-button" id="move-action">Move Entry</button>
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      
      const handleAction = (action: 'copy' | 'move' | null) => {
        document.body.removeChild(modal);
        resolve(action);
      };
      
      modal.addEventListener('click', (e) => {
        if (e.target === modal) handleAction(null);
      });
      
      document.getElementById('cancel-action')?.addEventListener('click', () => handleAction(null));
      document.getElementById('copy-action')?.addEventListener('click', () => handleAction('copy'));
      document.getElementById('move-action')?.addEventListener('click', () => handleAction('move'));
    });
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
          <button onClick={() => loadData()}>Retry</button>
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
          <button 
            onClick={refreshEntries} 
            className="refresh-button"
            title="Refresh entries from server"
          >
            ⟳ Refresh
          </button>
          <label className="weekend-toggle">
            <input
              type="checkbox"
              checked={includeWeekends}
              onChange={(e) => setIncludeWeekends(e.target.checked)}
            />
            <span>Include weekends</span>
          </label>
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

      <div className="timesheet-container">
        <div className={`timesheet-grid ${includeWeekends ? 'weekends-included' : 'weekdays-only'}`}>
          {weekDays.map(day => {
            const dayEntries = getEntriesForDate(day.date);
            const totalMinutes = getTotalMinutesForDate(day.date);
            const billableMinutes = getBillableMinutesForDate(day.date);
            const nonBillableMinutes = getNonBillableMinutesForDate(day.date);
            
            return (
              <div 
                key={day.date} 
                className={`day-column ${day.isToday ? 'today' : ''} ${day.isWeekend ? 'weekend' : ''} ${dragOverDate === day.date ? 'drag-over' : ''}`}
                onDragOver={(e) => handleDragOver(e, day.date)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, day.date)}
                onClick={(e) => {
                  // Only open add entry if clicking on empty space, not on an entry
                  if ((e.target as HTMLElement).classList.contains('day-entries') || 
                      (e.target as HTMLElement).classList.contains('day-column')) {
                    openAddEntry(day.date);
                  }
                }}
              >
                <div className="day-header">
                  <div className="day-info">
                    <div className="day-name">{day.dayName}</div>
                    <div className="day-date">
                      <span className="day-number">{day.dayNumber}</span>
                      <span className="day-month">{day.monthName}</span>
                    </div>
                  </div>
                  {totalMinutes > 0 && (
                    <div className="day-totals">
                      <div className="day-total-badge total" title="Total hours">
                        {formatDuration(totalMinutes)}
                      </div>
                      {billableMinutes > 0 && (
                        <div className="day-total-badge billable" title="Billable hours">
                          {formatDuration(billableMinutes)}
                        </div>
                      )}
                      {nonBillableMinutes > 0 && (
                        <div className="day-total-badge non-billable" title="Non-billable hours">
                          {formatDuration(nonBillableMinutes)}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                <div className="day-entries">
                  {dayEntries.map((entry, index) => {
                    const entryMinutes = entry.minutes || entry.durationInMinutes || 0;
                    const entryId = entry.id || entry.timeEntryId || `entry-${index}`;
                    
                    return (
                      <div 
                        key={entryId} 
                        className="time-entry-card"
                        draggable
                        onDragStart={(e) => handleDragStart(e, entry)}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="entry-header">
                          <div className="entry-duration">
                            {formatDuration(entryMinutes)}
                          </div>
                          <div className="entry-actions">
                            <button 
                              onClick={() => openEditEntry(entry)}
                              className="entry-action-btn edit"
                              title="Edit entry"
                            >
                              ✎
                            </button>
                            <button 
                              onClick={() => duplicateEntry(entry)}
                              className="entry-action-btn duplicate"
                              title="Duplicate entry"
                            >
                              ⎘
                            </button>
                            <button 
                              onClick={() => handleDeleteEntry(entry)}
                              className="entry-action-btn delete"
                              title="Delete entry"
                            >
                              ×
                            </button>
                          </div>
                        </div>
                        <div className="entry-project">
                          {entry.task?.project?.projectName || 
                           entry.project?.projectName || 
                           'Ad-hoc Activity'}
                        </div>
                        <div className="entry-task">
                          {entry.task?.taskName || 
                           entry.activity_name ||
                           entry.activityName ||
                           'General Work'}
                        </div>
                        {(entry.notes) && (
                          <div className="entry-notes">
                            {entry.notes}
                          </div>
                        )}
                        <div className="entry-footer">
                          {entry.billable && <span className="entry-badge billable">Billable</span>}
                          {entry.category && (
                            <span className="entry-badge category">
                              {entry.category.categoryName || entry.category.name}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                <button 
                  className="add-entry-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    openAddEntry(day.date);
                  }}
                >
                  + Add Entry
                </button>
                
                {dayEntries.length > 0 && (
                  <button 
                    className="delete-all-button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteAllEntries(day.date);
                    }}
                    title={`Delete all entries for ${day.dayName}`}
                  >
                    Delete All Entries
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {showAddEntry && (
        <div className="modal-overlay" onClick={() => setShowAddEntry(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>{editingEntry ? 'Edit Time Entry' : 'Add Time Entry'}</h2>
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
                  <option key={project.projectId} value={String(project.projectId)}>
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
                  <option value="">
                    {filteredTasks.length === 0 
                      ? "No tasks available for this project" 
                      : "Select a task..."}
                  </option>
                  {filteredTasks.map(task => (
                    <option key={task.taskId} value={String(task.taskId)}>
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
              <button onClick={handleSaveEntry} className="save-button">
                {editingEntry ? 'Update Entry' : 'Add Entry'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Timesheets;