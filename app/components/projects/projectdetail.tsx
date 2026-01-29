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

interface ProjectDetailViewProps {
  project: Project;
  onBack?: () => void;
  onSave?: (project: Project) => void;
}

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

  // Track changes
  const [hasChanges, setHasChanges] = useState(false);
  const [showSaveToast, setShowSaveToast] = useState(false);
  const [savedState, setSavedState] = useState({ tasks: project.tasks, notes: project.notes });

  useEffect(() => {
    const tasksChanged = JSON.stringify(tasks) !== JSON.stringify(savedState.tasks);
    const notesChanged = notes !== savedState.notes;
    setHasChanges(tasksChanged || notesChanged);
  }, [tasks, notes, savedState]);

  const completedTasks = tasks.filter((t) => t.completed);
  const pendingTasks = tasks.filter((t) => !t.completed);
  const progress = tasks.length
    ? Math.round((completedTasks.length / tasks.length) * 100)
    : 0;

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
      },
    ]);
    setNewTask('');
  };

  const handleSave = () => {
    setSavedState({ tasks, notes });
    setHasChanges(false);
    setShowSaveToast(true);
    onSave?.({ ...project, tasks, notes });
    setTimeout(() => setShowSaveToast(false), 2000);
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
              <button type="button" className={styles.actionBtn}>
                <Edit3 size={14} /> Edit
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
              <span className={styles.metaAccent}>{project.deadline}</span>
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
                          {task.dueDate && (
                            <span className={styles.taskMetaItem}>
                              <Calendar size={12} /> {task.dueDate}
                            </span>
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

                      {(task.subtasks?.length > 0 || task.blocker) && (
                        <button
                          type="button"
                          className={styles.expandBtn}
                          onClick={() => setExpandedTask(isExpanded ? null : task.id)}
                        >
                          {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
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
            <div className={styles.filesGrid}>
              {project.links.map((link) => (
                <a key={link.id} href={link.url} className={styles.fileCard}>
                  <div className={`${styles.fileIcon} ${link.type === 'file' ? styles.fileIconDoc : styles.fileIconLink}`}>
                    {link.type === 'file' ? <FileText size={20} /> : <LinkIcon size={20} />}
                  </div>
                  <div className={styles.fileMeta}>
                    <div className={styles.fileTitle}>{link.title}</div>
                    <div className={styles.fileType}>{link.type === 'file' ? 'Document' : 'Link'}</div>
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