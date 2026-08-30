import { useEffect, useState } from "react";

import {
  getTask,
  listExercisesForTask,
  listKnowledgePoints,
  listTasks,
  recordEvent,
} from "../api/client";
import type { Exercise, KnowledgePoint, LearningEvent, TaskTemplate } from "../api/types";
import { taskTypeLabel, TASK_TYPE_META } from "./taskMeta";

type Props = {
  loadTasks?: () => Promise<TaskTemplate[]>;
  loadTask?: (taskId: string) => Promise<TaskTemplate>;
  loadKnowledgePoints?: () => Promise<KnowledgePoint[]>;
  loadExercises?: (taskId: string) => Promise<Exercise[]>;
  recordLearningEvent?: (event: LearningEvent) => Promise<LearningEvent>;
};

const EXERCISE_TYPE_LABEL: Record<Exercise["exercise_type"], string> = {
  single_choice: "单选",
  multiple_choice: "多选",
  short_answer: "简答",
  analysis: "分析",
  design: "设计",
};

const COURSE_ID = "computer-networks";
const USER_ID = "student-demo";

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `evt-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

async function recordTaskOpened(
  task: TaskTemplate,
  saveEvent: (event: LearningEvent) => Promise<LearningEvent>,
): Promise<void> {
  try {
    await saveEvent({
      course_id: COURSE_ID,
      user_id: USER_ID,
      event_id: newId(),
      event_type: "task_opened",
      object_id: task.task_id,
      occurred_at: new Date().toISOString(),
      payload: { task_type: task.task_type },
    });
  } catch {
    // 事件记录失败静默忽略。
  }
}

export function TaskWorkspace({
  loadTasks = listTasks,
  loadTask = getTask,
  loadKnowledgePoints = listKnowledgePoints,
  loadExercises = listExercisesForTask,
  recordLearningEvent = recordEvent,
}: Props) {
  const [knowledgePoints, setKnowledgePoints] = useState<Record<string, KnowledgePoint>>({});
  const [tasks, setTasks] = useState<TaskTemplate[]>([]);
  const [selected, setSelected] = useState<TaskTemplate | null>(null);
  const [exercises, setExercises] = useState<{ taskId: string; items: Exercise[] } | null>(
    null,
  );
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(new Set());
  const [completionSubmitting, setCompletionSubmitting] = useState<string | null>(null);
  const [completionError, setCompletionError] = useState("");

  useEffect(() => {
    let active = true;
    loadKnowledgePoints()
      .then((items) => {
        if (!active) return;
        setKnowledgePoints(
          Object.fromEntries(items.map((item) => [item.knowledge_point_id, item])),
        );
      })
      .catch(() => {
        // 知识点加载失败时回退为显示原始 ID，不影响任务浏览。
      });
    return () => {
      active = false;
    };
  }, [loadKnowledgePoints]);

  useEffect(() => {
    let active = true;
    loadTasks()
      .then(async (items) => {
        if (!active) return;
        setTasks(items);
        if (items[0]) {
          const detail = await loadTask(items[0].task_id);
          if (active) setSelected(detail);
        }
      })
      .catch((caught) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : "任务加载失败。");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [loadTask, loadTasks]);

  // 试题按任务标识缓存，切换任务时不会短暂显示上一个任务的试题。
  useEffect(() => {
    if (!selected) return;
    const taskId = selected.task_id;
    let active = true;
    loadExercises(taskId)
      .then((items) => {
        if (active) setExercises({ taskId, items });
      })
      .catch(() => {
        // 试题加载失败时回退为显示 exercise_ids，不影响任务浏览。
        if (active) setExercises({ taskId, items: [] });
      });
    return () => {
      active = false;
    };
  }, [loadExercises, selected]);

  async function selectTask(taskId: string) {
    setError("");
    setCompletionError("");
    try {
      const detail = await loadTask(taskId);
      setSelected(detail);
      void recordTaskOpened(detail, recordLearningEvent);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "任务加载失败。");
    }
  }

  async function completeTask(task: TaskTemplate) {
    if (completionSubmitting || completedTaskIds.has(task.task_id)) return;
    setCompletionSubmitting(task.task_id);
    setCompletionError("");
    try {
      await recordLearningEvent({
        course_id: COURSE_ID,
        user_id: USER_ID,
        event_id: newId(),
        event_type: "task_completed",
        object_id: task.task_id,
        occurred_at: new Date().toISOString(),
        payload: { task_type: task.task_type },
      });
      setCompletedTaskIds((current) => new Set(current).add(task.task_id));
    } catch (caught) {
      setCompletionError(
        caught instanceof Error ? caught.message : "任务完成状态提交失败，请重试。",
      );
    } finally {
      setCompletionSubmitting(null);
    }
  }

  return (
    <section className="panel tasks-panel" aria-labelledby="tasks-title">
      <div className="panel__heading">
        <div>
          <span className="eyebrow">任务引擎</span>
          <h2 id="tasks-title">六类教学任务</h2>
        </div>
        <span className="badge badge--warm">{loading ? "…" : tasks.length}</span>
      </div>

      {error && <p className="error-message">{error}</p>}

      <div className="task-workspace">
        <div className="task-list" aria-label="任务列表">
          {tasks.map((task) => (
            <button
              key={task.task_id}
              type="button"
              className={`task-card${
                selected?.task_id === task.task_id ? " task-card--selected" : ""
              }`}
              onClick={() => void selectTask(task.task_id)}
            >
              <span
                className={`task-type-badge task-type-badge--${TASK_TYPE_META[task.task_type]?.tone ?? "green"}`}
              >
                {taskTypeLabel(task.task_type)}
              </span>
              <div className="task-card-content">
                <strong className="task-card-title">{task.title}</strong>
                <p className="task-card-description">
                  {task.description || TASK_TYPE_META[task.task_type]?.goal}
                </p>
              </div>
              <div className="task-card-footer">
                <span className="task-card-steps">
                  {(TASK_TYPE_META[task.task_type]?.flow ?? []).length} 个学习步骤
                </span>
                <span className="task-card-arrow" aria-hidden="true">
                  →
                </span>
              </div>
            </button>
          ))}
        </div>

        <div className="task-detail">
          {selected ? (
            <TaskDetail
              task={selected}
              knowledgePoints={knowledgePoints}
              exercises={exercises?.taskId === selected.task_id ? exercises.items : []}
              completed={completedTaskIds.has(selected.task_id)}
              submitting={completionSubmitting === selected.task_id}
              completionError={completionError}
              onComplete={() => void completeTask(selected)}
            />
          ) : (
            <div className="empty-state">正在读取任务详情…</div>
          )}
        </div>
      </div>
    </section>
  );
}

function TaskDetail({
  task,
  knowledgePoints,
  exercises,
  completed,
  submitting,
  completionError,
  onComplete,
}: {
  task: TaskTemplate;
  knowledgePoints: Record<string, KnowledgePoint>;
  exercises: Exercise[];
  completed: boolean;
  submitting: boolean;
  completionError: string;
  onComplete: () => void;
}) {
  const meta = TASK_TYPE_META[task.task_type];
  return (
    <>
      <div className="task-detail__head">
        <span className={`task-type-badge task-type-badge--${meta?.tone ?? "green"}`}>
          {taskTypeLabel(task.task_type)}
        </span>
        <h3>{task.title}</h3>
        <p className="task-detail__goal">{meta?.goal}</p>
      </div>

      <p className="task-detail__desc">{task.description}</p>

      <FlowSteps steps={meta?.flow ?? []} />

      <div className="task-detail__grid">
        <KnowledgePointList
          knowledgePointIds={task.knowledge_point_ids}
          knowledgePoints={knowledgePoints}
        />
        <DetailList title="关联资料" items={task.resource_ids} />
        <ExerciseList exerciseIds={task.exercise_ids ?? []} exercises={exercises} />
        <DetailList title="完成判据" items={task.completion_criteria} />
        <DetailList title="AI 反馈介入点" items={task.ai_feedback_points} />
      </div>

      <div className="task-detail__footer">
        <span>{completed ? "已完成这项学习任务。" : "准备好开始这项学习任务了吗？"}</span>
        <button type="button" onClick={onComplete} disabled={completed || submitting}>
          {completed ? "已完成" : submitting ? "正在提交…" : "标记完成"}
        </button>
        {completionError && <p className="task-completion__error">{completionError}</p>}
      </div>
    </>
  );
}

function FlowSteps({ steps }: { steps: string[] }) {
  if (steps.length === 0) return null;
  return (
    <div className="flow-steps" aria-label="任务流程">
      <h4>任务流程</h4>
      <ol>
        {steps.map((step, index) => (
          <li key={step}>
            <span className="flow-steps__index">{index + 1}</span>
            <span>{step}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** 把任务引用的知识点 ID 解析为可读的知识点名称、章节与先修关系。 */
function KnowledgePointList({
  knowledgePointIds,
  knowledgePoints,
}: {
  knowledgePointIds: string[];
  knowledgePoints: Record<string, KnowledgePoint>;
}) {
  return (
    <div className="detail-list">
      <h4>关联知识点</h4>
      <ul>
        {knowledgePointIds.map((id) => {
          const point = knowledgePoints[id];
          if (!point) {
            return <li key={id}>{id}</li>;
          }
          const prerequisites = (point.prerequisite_ids ?? [])
            .map((prerequisiteId) => knowledgePoints[prerequisiteId]?.name ?? prerequisiteId)
            .join("、");
          return (
            <li key={id}>
              <strong className="knowledge-point__name">{point.name}</strong>
              <span className="knowledge-point__chapter">{point.chapter}</span>
              {prerequisites && (
                <span className="knowledge-point__prereq">先修：{prerequisites}</span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/** 展示任务关联的试题，使「任务 → 知识点 → 资料 → 试题」的引用链在界面上可见。 */
function ExerciseList({
  exerciseIds,
  exercises,
}: {
  exerciseIds: string[];
  exercises: Exercise[];
}) {
  if (exerciseIds.length === 0) return null;
  const loaded = new Map(exercises.map((exercise) => [exercise.exercise_id, exercise]));
  return (
    <div className="detail-list">
      <h4>关联试题</h4>
      <ul>
        {exerciseIds.map((id) => {
          const exercise = loaded.get(id);
          if (!exercise) {
            return <li key={id}>{id}</li>;
          }
          return (
            <li key={id}>
              <strong className="exercise__question">{exercise.question}</strong>
              <span className="exercise__meta">
                {EXERCISE_TYPE_LABEL[exercise.exercise_type] ?? exercise.exercise_type}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function DetailList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="detail-list">
      <h4>{title}</h4>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
