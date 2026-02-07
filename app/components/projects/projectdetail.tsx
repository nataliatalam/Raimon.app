'use client';

import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Check,
  Clock,
  Flame,
  Plus,
  Paperclip,
  FileText,
  Link as LinkIcon,
  LayoutGrid,
  Calendar,
  Pause,
  Target,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Repeat,
  GitBranch,
  X,
  Edit3,
} from 'lucide-react';
import styles from './Projectdetail.module.css';

/* ─────────────────────────────────────────────────────────── */
/* Types                                                        */
/* ─────────────────────────────────────────────────────────── */

interface Subtask {
  id: string;
  title: string;
  completed: boolean;
}

interface Task {
  id: string;
  title: string;
  completed: boolean;
  dueDate?: string;
  priority?: 'high' | 'medium' | 'low';
  subtasks: Subtask[];
  dependsOn?: string;
  blocker?: string;
  recurring?: string;
  note?: string;
}

interface ProjectLink {
  id: string;
  title: string;
  url: string;
  type: 'file' | 'link';
}

interface ActivityItem {
  id: string;
  action: string;
  detail: string;
  time: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
  type: 'work' | 'personal';
  status: 'active' | 'paused' | 'completed';
  color: string;
  timeframe: string;
  deadline: string;
  tasks: Task[];
  notes: string;
  motivations: string[];
  links: ProjectLink[];
  activity: ActivityItem[];
}

type SavedSnapshot = {
  tasks: Task[];
  notes: string;
  name: string;
  description: string;
  type: Project['type'];
  timeframe: string;
  deadline: string;
  motivations: string[];
};

interface ProjectDetailViewProps {
  project: Project;
  onBack?: () => void;
  onSave?: (project: Project) => void;
}

const toDatePart = (value?: string) => {
  if (!value) return '';
  return value.slice(0, 10);
};

const toTimePart = (value?: string) => {
  if (!value) return '';
  const [, time] = value.split('T');
  return (time ?? '').slice(0, 5);
};

const buildDateTimeValue = (date?: string, time?: string) => {
  if (!date) return '';
  const safeTime = time && time.length > 0 ? time : '23:59';
  return `${date}T${safeTime}:00`;
};

/* ─────────────────────────────────────────────────────────── */
/* Component                                                    */
/* ─────────────────────────────────────────────────────────── */

export default function ProjectDetailView({
  project,
  onBack,
  onSave,
}: ProjectDetailViewProps) {
  const [tasks, setTasks] = useState<Task[]>(project.tasks);
  const [notes, setNotes] = useState(project.notes);
  const [newTask, setNewTask] = useState('');
  const [showCompleted, setShowCompleted] = useState(false);
  const [activeTab, setActiveTab] = useState<'tasks' | 'notes' | 'files' | 'activity'>('tasks');
  const [expandedTask, setExpandedTask] = useState<string | null>(null);
  const [editingTaskNote, setEditingTaskNote] = useState<string | null>(null);

  // Links state
  const [links, setLinks] = useState<ProjectLink[]>(project.links);
  const [newLinkUrl, setNewLinkUrl] = useState('');
  const [newLinkTitle, setNewLinkTitle] = useState('');

  // Edit mode state
  const [isEditMode, setIsEditMode] = useState(false);
  const [editName, setEditName] = useState(project.name);
  const [editDescription, setEditDescription] = useState(project.description);
  const [editType, setEditType] = useState<'work' | 'personal'>(project.type);
  const [editTimeframe, setEditTimeframe] = useState(project.timeframe);
  const [editDeadline, setEditDeadline] = useState(project.deadline);
  const [editMotivations, setEditMotivations] = useState<string[]>(project.motivations);

  // Track changes
  const initialSnapshot: SavedSnapshot = {
    tasks: project.tasks,
    notes: project.notes,
    name: project.name,
    description: project.description,
    type: project.type,
    timeframe: project.timeframe,
    deadline: project.deadline,
    motivations: project.motivations,
  };
  const [hasChanges, setHasChanges] = useState(false);
  const [showSaveToast, setShowSaveToast] = useState(false);
  const [savedState, setSavedState] = useState<SavedSnapshot>(initialSnapshot);

  useEffect(() => {
    setTasks(project.tasks);
    setNotes(project.notes);
    setLinks(project.links);
    setEditName(project.name);
    setEditDescription(project.description);
    setEditType(project.type);
    setEditTimeframe(project.timeframe);
    setEditDeadline(project.deadline);
    setEditMotivations(project.motivations);
    setSavedState({
      tasks: project.tasks,
      notes: project.notes,
      name: project.name,
      description: project.description,
      type: project.type,
      timeframe: project.timeframe,
      deadline: project.deadline,
      motivations: project.motivations,
    });
  }, [project]);

  useEffect(() => {
    const snapshot: SavedSnapshot = {
      tasks,
      notes,
      name: editName,
      description: editDescription,
      type: editType,
      timeframe: editTimeframe,
      deadline: editDeadline,
      motivations: editMotivations,
    };
    setHasChanges(JSON.stringify(snapshot) !== JSON.stringify(savedState));
  }, [tasks, notes, editName, editDescription, editType, editTimeframe, editDeadline, editMotivations, savedState]);

  const formatDateLabel = (value?: string) => {
    if (!value) return '';
    const normalized = value.includes('T') ? value : `${value}T00:00:00`;
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return '';
    const dateString = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    const timeString = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    return `${dateString} • ${timeString}`;
  };

  const completedTasks = tasks.filter((t) => t.completed);
  const pendingTasks = tasks.filter((t) => !t.completed);
  const progress = tasks.length
    ? Math.round((completedTasks.length / tasks.length) * 100)
    : 0;
  const projectDeadlineLabel = project.deadline ? formatDateLabel(project.deadline) || 'No deadline' : 'No deadline';
  const editDeadlineDate = toDatePart(editDeadline);
  const editDeadlineTime = toTimePart(editDeadline);

  const toggleTask = (id: string) => {
    setTasks(tasks.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t)));
  };

  const toggleSubtask = (taskId: string, subtaskId: string) => {
    setTasks(
      tasks.map((t) => {
        if (t.id === taskId) {
          return {
            ...t,
            subtasks: t.subtasks.map((st) =>
              st.id === subtaskId ? { ...st, completed: !st.completed } : st
            ),
          };
        }
        return t;
      })
    );
  };

  const addTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTask.trim()) return;
    setTasks([
      ...tasks,
      {
        id: Date.now().toString(),
        title: newTask,
        completed: false,
        subtasks: [],
        dueDate: '',
        note: '',
      },
    ]);
    setNewTask('');
  };

  const updateTaskNote = (taskId: string, note: string) => {
    setTasks(tasks.map((t) => (t.id === taskId ? { ...t, note } : t)));
  };

  const addLink = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLinkUrl.trim()) return;
    const newLink: ProjectLink = {
      id: Date.now().toString(),
      title: newLinkTitle.trim() || newLinkUrl.trim(),
      url: newLinkUrl.trim(),
      type: 'link',
    };
    setLinks([...links, newLink]);
    setNewLinkUrl('');
    setNewLinkTitle('');
  };

  const removeLink = (linkId: string) => {
    setLinks(links.filter((l) => l.id !== linkId));
  };

  const toggleEditMode = () => {
    if (isEditMode) {
      // Reset to original values when canceling
      setEditName(project.name);
      setEditDescription(project.description);
      setEditType(project.type);
      setEditTimeframe(project.timeframe);
      setEditDeadline(project.deadline);
      setEditMotivations(project.motivations);
    }
    setIsEditMode(!isEditMode);
  };

  const toggleMotivation = (motivation: string) => {
    setEditMotivations((prev) =>
      prev.includes(motivation)
        ? prev.filter((m) => m !== motivation)
        : [...prev, motivation]
    );
  };

  const handleSave = () => {
    const snapshot: SavedSnapshot = {
      tasks,
      notes,
      name: editName,
      description: editDescription,
      type: editType,
      timeframe: editTimeframe,
      deadline: editDeadline,
      motivations: editMotivations,
    };
    setSavedState(snapshot);
    setHasChanges(false);
    setShowSaveToast(true);
    onSave?.({
      ...project,
      name: editName,
      description: editDescription,
      type: editType,
      timeframe: editTimeframe,
      deadline: editDeadline,
      motivations: editMotivations,
      tasks,
      notes,
      links,
    });
    setTimeout(() => setShowSaveToast(false), 2000);
  };

  const handleProjectDeadlineDateChange = (value: string) => {
    if (!value) {
      setEditDeadline('');
      return;
    }
    setEditDeadline(buildDateTimeValue(value, editDeadlineTime));
  };

  const handleProjectDeadlineTimeChange = (value: string) => {
    if (!editDeadlineDate) return;
    setEditDeadline(buildDateTimeValue(editDeadlineDate, value));
  };

  const handleTaskDeadlineChange = (taskId: string, datePart?: string, timePart?: string) => {
    setTasks(prev =>
      prev.map((task) => {
        if (task.id !== taskId) return task;
        const currentDate = datePart !== undefined ? datePart : toDatePart(task.dueDate);
        const currentTime = timePart !== undefined ? timePart : toTimePart(task.dueDate);
        const combined = currentDate ? buildDateTimeValue(currentDate, currentTime) : '';
        return { ...task, dueDate: combined };
      }),
    );
  };

  const handleBack = () => {
    if (hasChanges) {
      setShowSaveToast(true);
    } else {
      onBack?.();
    }
  };

  const getDependency = (id: string) => tasks.find((t) => t.id === id);

  const getPriorityClass = (priority?: string) => {
    switch (priority) {
      case 'high':
        return styles.priorityHigh;
      case 'medium':
        return styles.priorityMedium;
      case 'low':
        return styles.priorityLow;
      default:
        return '';
    }
  };

  return (
    <div className={styles.page}>
      {/* Save Toast */}
      {showSaveToast && hasChanges && (
        <div className={styles.toast}>
          <span>You have unsaved changes</span>
          <button type="button" className={styles.toastSaveBtn} onClick={handleSave}>
            Save Changes
          </button>
          <button
            type="button"
            className={styles.toastCloseBtn}
            onClick={() => {
              setShowSaveToast(false);
              onBack?.();
            }}
            title="Discard and go back"
          >
            <X size={18} />
          </button>
        </div>
      )}

      {/* Saved Confirmation */}
      {showSaveToast && !hasChanges && (
        <div className={styles.toastSuccess}>
          <Check size={18} />
          <span>Changes saved</span>
        </div>
      )}

      {/* Nav */}
      <nav className={styles.nav}>
        <span className={styles.navBrand}>Raimon Workspace</span>
        <div className={styles.navActions}>
          <button type="button" className={styles.navBtn}>
            <LayoutGrid size={20} />
          </button>
          <button type="button" className={styles.navBtn}>
            <Calendar size={20} />
          </button>
        </div>
      </nav>

      <div className={styles.container}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerTop}>
            <button type="button" className={styles.backBtn} onClick={handleBack}>
              <ArrowLeft size={16} /> My Projects
            </button>
            <div className={styles.headerActions}>
              <button type="button" className={styles.actionBtn}>
                <Pause size={14} /> Pause
              </button>
              <button
                type="button"
                className={`${styles.actionBtn} ${isEditMode ? styles.actionBtnActive : ''}`}
                onClick={toggleEditMode}
              >
                <Edit3 size={14} /> {isEditMode ? 'Cancel' : 'Edit'}
              </button>
              {hasChanges && (
                <button type="button" className={styles.saveBtn} onClick={handleSave}>
                  Save Changes
                </button>
              )}
            </div>
          </div>

          {/* Title + Progress */}
          <div className={styles.heroRow}>
            <div className={styles.heroContent}>
              {isEditMode ? (
                <>
                  {/* Edit Mode - Type Toggle */}
                  <div className={styles.editTypeToggle}>
                    <button
                      type="button"
                      className={`${styles.editTypeBtn} ${editType === 'work' ? styles.editTypeBtnActive : ''}`}
                      onClick={() => setEditType('work')}
                    >
                      Work
                    </button>
                    <button
                      type="button"
                      className={`${styles.editTypeBtn} ${editType === 'personal' ? styles.editTypeBtnActive : ''}`}
                      onClick={() => setEditType('personal')}
                    >
                      Personal
                    </button>
                  </div>

                  {/* Edit Mode - Project Name */}
                  <input
                    type="text"
                    className={styles.editTitleInput}
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="Project name..."
                  />

                  {/* Edit Mode - Description */}
                  <textarea
                    className={styles.editDescriptionInput}
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    placeholder="Project description..."
                    rows={2}
                  />

                  {/* Edit Mode - Motivations */}
                  <div className={styles.editMotivationsSection}>
                    <span className={styles.editLabel}>Why are you doing this?</span>
                    <div className={styles.editMotivationsGrid}>
                      {['Make money', 'Creative output', 'Health', 'Joy', 'Family', 'Growth'].map((m) => (
                        <button
                          key={m}
                          type="button"
                          className={`${styles.editMotivationBtn} ${editMotivations.includes(m) ? styles.editMotivationBtnActive : ''}`}
                          onClick={() => toggleMotivation(m)}
                        >
                          <Flame size={12} /> {m}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Edit Mode - Timeline & Deadline */}
                  <div className={styles.editTimeSection}>
                    <div className={styles.editField}>
                      <span className={styles.editLabel}>Timeframe</span>
                      <select
                        className={styles.editSelect}
                        value={editTimeframe}
                        onChange={(e) => setEditTimeframe(e.target.value)}
                      >
                        <option value="Today">Today</option>
                        <option value="This Week">This Week</option>
                        <option value="This Month">This Month</option>
                        <option value="Long-term">Long-term</option>
                      </select>
                    </div>
                    <div className={styles.editField}>
                      <span className={styles.editLabel}>Deadline</span>
                      <div className={styles.editDeadlineRow}>
                        <input
                          type="date"
                          className={styles.editDeadlineInput}
                          value={editDeadlineDate}
                          onChange={(e) => handleProjectDeadlineDateChange(e.target.value)}
                        />
                        <input
                          type="time"
                          className={styles.editDeadlineInput}
                          value={editDeadlineTime}
                          onChange={(e) => handleProjectDeadlineTimeChange(e.target.value)}
                          disabled={!editDeadlineDate}
                        />
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className={styles.badges}>
                    <span className={`${styles.typeBadge} ${project.type === 'work' ? styles.typeBadgeWork : styles.typeBadgePersonal}`}>
                      {project.type}
                    </span>
                    {project.motivations.map((m) => (
                      <span key={m} className={styles.motivationBadge}>
                        <Flame size={12} /> {m}
                      </span>
                    ))}
                  </div>
                  <h1 className={styles.title}>{project.name}</h1>
                  <p className={styles.description}>{project.description}</p>
                </>
              )}
            </div>

            {/* Progress Ring */}
            <div className={styles.progressRing}>
              <svg width="88" height="88" className={styles.progressSvg}>
                <circle cx="44" cy="44" r="36" className={styles.progressTrack} />
                <circle
                  cx="44"
                  cy="44"
                  r="36"
                  className={styles.progressFill}
                  strokeDasharray={226}
                  strokeDashoffset={226 - (226 * progress) / 100}
                />
              </svg>
              <div className={styles.progressValue}>{progress}%</div>
            </div>
          </div>

          {/* Meta Pills */}
          <div className={styles.metaPills}>
            <div className={styles.metaPill}>
              <Clock size={15} />
              <span>{project.timeframe}</span>
              <span className={styles.metaDivider} />
              <span className={styles.metaAccent}>{projectDeadlineLabel}</span>
            </div>
            <div className={styles.metaPill}>
              <Target size={15} />
              <span>{completedTasks.length}/{tasks.length} tasks</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          {(['tasks', 'notes', 'files', 'activity'] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              className={`${styles.tab} ${activeTab === tab ? styles.tabActive : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tasks Tab */}
        {activeTab === 'tasks' && (
          <div className={styles.card}>
            {/* Add Task */}
            <form onSubmit={addTask} className={styles.addTaskForm}>
              <Plus size={20} className={styles.addTaskIcon} />
              <input
                type="text"
                className={styles.addTaskInput}
                placeholder="Add a new task..."
                value={newTask}
                onChange={(e) => setNewTask(e.target.value)}
              />
              <button type="submit" className={styles.addTaskBtn}>
                Add
              </button>
            </form>

            {/* Pending Tasks */}
            <div className={styles.taskSection}>
              <div className={styles.taskSectionHeader}>To Do ({pendingTasks.length})</div>

              {pendingTasks.map((task) => {
                const dependency = task.dependsOn ? getDependency(task.dependsOn) : null;
                const isExpanded = expandedTask === task.id;
                const subtaskProgress = task.subtasks?.length
                  ? Math.round(
                      (task.subtasks.filter((s) => s.completed).length / task.subtasks.length) * 100
                    )
                  : 0;
                const taskDatePart = toDatePart(task.dueDate);
                const taskTimePart = toTimePart(task.dueDate);

                return (
                  <div key={task.id} className={styles.taskCard}>
                    <div className={`${styles.taskRow} ${getPriorityClass(task.priority)}`}>
                      <button
                        type="button"
                        className={styles.checkbox}
                        onClick={() => toggleTask(task.id)}
                      />

                      <div className={styles.taskContent}>
                        <div className={styles.taskTitleRow}>
                          <span className={styles.taskTitle}>{task.title}</span>
                          {task.recurring && (
                            <span className={styles.recurringBadge}>
                              <Repeat size={10} /> {task.recurring}
                            </span>
                          )}
                        </div>

                        <div className={styles.taskMeta}>
                          {isEditMode ? (
                            <span className={styles.taskMetaItem}>
                              <Calendar size={12} />
                              <div className={styles.taskDeadlineControls}>
                                <input
                                  type="date"
                                  className={styles.taskDeadlineInput}
                                  value={taskDatePart}
                                  onChange={(e) => handleTaskDeadlineChange(task.id, e.target.value, undefined)}
                                />
                                <input
                                  type="time"
                                  className={styles.taskDeadlineInput}
                                  value={taskTimePart}
                                  onChange={(e) => handleTaskDeadlineChange(task.id, undefined, e.target.value)}
                                  disabled={!taskDatePart}
                                />
                              </div>
                            </span>
                          ) : (
                            task.dueDate && (
                              <span className={styles.taskMetaItem}>
                                <Calendar size={12} /> {formatDateLabel(task.dueDate)}
                              </span>
                            )
                          )}
                          {task.subtasks?.length > 0 && (
                            <span className={styles.taskMetaItem}>
                              {task.subtasks.filter((s) => s.completed).length}/{task.subtasks.length} subtasks
                            </span>
                          )}
                          {dependency && !dependency.completed && (
                            <span className={styles.dependencyBadge}>
                              <GitBranch size={10} /> Waiting on: {dependency.title.slice(0, 20)}...
                            </span>
                          )}
                          {task.blocker && (
                            <span className={styles.blockerBadge}>
                              <AlertTriangle size={10} /> Blocked
                            </span>
                          )}
                        </div>
                      </div>

                      {(task.subtasks?.length > 0 || task.blocker || task.note !== undefined) && (
                        <button
                          type="button"
                          className={styles.expandBtn}
                          onClick={() => setExpandedTask(isExpanded ? null : task.id)}
                        >
                          {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </button>
                      )}
                      {!task.note && task.note !== '' && !isExpanded && (
                        <button
                          type="button"
                          className={styles.addNoteBtn}
                          onClick={() => {
                            setExpandedTask(task.id);
                            setEditingTaskNote(task.id);
                          }}
                          title="Add note"
                        >
                          <FileText size={14} />
                        </button>
                      )}
                    </div>

                    {/* Expanded */}
                    {isExpanded && (
                      <div className={styles.taskExpanded}>
                        {task.blocker && (
                          <div className={styles.blockerAlert}>
                            <AlertTriangle size={16} />
                            <div>
                              <div className={styles.blockerLabel}>Blocker</div>
                              <div className={styles.blockerText}>{task.blocker}</div>
                            </div>
                          </div>
                        )}

                        {/* Task Note Section */}
                        <div className={styles.taskNoteSection}>
                          <div className={styles.taskNoteHeader}>
                            <FileText size={14} />
                            <span>Note</span>
                            <button
                              type="button"
                              className={styles.taskNoteCloseBtn}
                              onClick={() => setExpandedTask(null)}
                              title="Close"
                            >
                              <X size={14} />
                            </button>
                          </div>
                          {editingTaskNote === task.id ? (
                            <div className={styles.taskNoteEdit}>
                              <textarea
                                className={styles.taskNoteInput}
                                value={task.note || ''}
                                onChange={(e) => updateTaskNote(task.id, e.target.value)}
                                placeholder="Add a note for this task..."
                                autoFocus
                              />
                              <button
                                type="button"
                                className={styles.taskNoteSaveBtn}
                                onClick={() => setEditingTaskNote(null)}
                              >
                                Done
                              </button>
                            </div>
                          ) : (
                            <div
                              className={styles.taskNoteDisplay}
                              onClick={() => setEditingTaskNote(task.id)}
                            >
                              {task.note ? (
                                <p className={styles.taskNoteText}>{task.note}</p>
                              ) : (
                                <p className={styles.taskNotePlaceholder}>Click to add a note...</p>
                              )}
                            </div>
                          )}
                        </div>

                        {task.subtasks?.length > 0 && (
                          <div className={styles.subtaskSection}>
                            <div className={styles.subtaskHeader}>
                              <span>Subtasks</span>
                              <div className={styles.subtaskProgress}>
                                <div className={styles.subtaskProgressTrack}>
                                  <div
                                    className={styles.subtaskProgressFill}
                                    style={{ width: `${subtaskProgress}%` }}
                                  />
                                </div>
                                <span>{subtaskProgress}%</span>
                              </div>
                            </div>
                            {task.subtasks.map((st) => (
                              <div key={st.id} className={styles.subtaskRow}>
                                <button
                                  type="button"
                                  className={`${styles.subtaskCheckbox} ${st.completed ? styles.subtaskChecked : ''}`}
                                  onClick={() => toggleSubtask(task.id, st.id)}
                                >
                                  {st.completed && <Check size={12} />}
                                </button>
                                <span className={st.completed ? styles.subtaskDone : ''}>
                                  {st.title}
                                </span>
                              </div>
                            ))}
                            <button type="button" className={styles.addSubtaskBtn}>
                              <Plus size={14} /> Add subtask
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Completed Tasks */}
            {completedTasks.length > 0 && (
              <div className={styles.taskSection}>
                <button
                  type="button"
                  className={styles.completedToggle}
                  onClick={() => setShowCompleted(!showCompleted)}
                >
                  <span>Completed ({completedTasks.length})</span>
                  {showCompleted ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
                {showCompleted &&
                  completedTasks.map((task) => (
                    <div key={task.id} className={styles.completedTask}>
                      <button
                        type="button"
                        className={styles.checkboxChecked}
                        onClick={() => toggleTask(task.id)}
                      >
                        <Check size={14} />
                      </button>
                      <span className={styles.completedTaskTitle}>{task.title}</span>
                    </div>
                  ))}
              </div>
            )}
          </div>
        )}

        {/* Notes Tab */}
        {activeTab === 'notes' && (
          <div className={styles.notesCard}>
            <textarea
              className={styles.notesTextarea}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Brain dump, meeting notes, or random thoughts..."
            />
          </div>
        )}

        {/* Files Tab */}
        {activeTab === 'files' && (
          <div className={styles.card}>
            {/* Files Section */}
            <div className={styles.filesSectionHeader}>Files</div>
            <div className={styles.filesGrid}>
              {links.filter((l) => l.type === 'file').map((link) => (
                <a key={link.id} href={link.url} className={styles.fileCard}>
                  <div className={`${styles.fileIcon} ${styles.fileIconDoc}`}>
                    <FileText size={20} />
                  </div>
                  <div className={styles.fileMeta}>
                    <div className={styles.fileTitle}>{link.title}</div>
                    <div className={styles.fileType}>Document</div>
                  </div>
                </a>
              ))}
            </div>
            <div className={styles.dropZone}>
              <Paperclip size={20} />
              <p>
                Drop files or <span>browse</span>
              </p>
            </div>

            {/* Links Section */}
            <div className={styles.linksSectionHeader}>
              <LinkIcon size={16} />
              <span>Links</span>
            </div>

            {/* Add Link Form */}
            <form onSubmit={addLink} className={styles.addLinkForm}>
              <input
                type="text"
                className={styles.addLinkInput}
                placeholder="https://"
                value={newLinkUrl}
                onChange={(e) => setNewLinkUrl(e.target.value)}
              />
              <input
                type="text"
                className={styles.addLinkTitleInput}
                placeholder="Title (optional)"
                value={newLinkTitle}
                onChange={(e) => setNewLinkTitle(e.target.value)}
              />
              <button type="submit" className={styles.addLinkBtn}>
                Add
              </button>
            </form>

            {/* Links List */}
            <div className={styles.linksGrid}>
              {links.filter((l) => l.type === 'link').length === 0 && (
                <p className={styles.noLinksText}>No links added yet</p>
              )}
              {links.filter((l) => l.type === 'link').map((link) => (
                <div key={link.id} className={styles.linkCard}>
                  <a href={link.url} target="_blank" rel="noopener noreferrer" className={styles.linkContent}>
                    <div className={`${styles.fileIcon} ${styles.fileIconLink}`}>
                      <LinkIcon size={20} />
                    </div>
                    <div className={styles.fileMeta}>
                      <div className={styles.fileTitle}>{link.title}</div>
                      <div className={styles.linkUrl}>{link.url}</div>
                    </div>
                  </a>
                  <button
                    type="button"
                    className={styles.removeLinkBtn}
                    onClick={() => removeLink(link.id)}
                    title="Remove link"
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <div className={styles.card}>
            <div className={styles.activityHeader}>Recent Activity</div>
            {project.activity.map((item) => (
              <div key={item.id} className={styles.activityRow}>
                <div className={styles.activityIcon}>
                  <Check size={14} />
                </div>
                <div className={styles.activityContent}>
                  <div className={styles.activityAction}>{item.action}</div>
                  <div className={styles.activityDetail}>{item.detail}</div>
                </div>
                <span className={styles.activityTime}>{item.time}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
