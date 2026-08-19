import { useEffect, useState } from "react";

import { getTask, listTasks, recordEvent } from "../api/client";
import type { TaskTemplate } from "../api/types";
import { taskTypeLabel, TASK_TYPE_META } from "./taskMeta";

type Props = {
  loadTasks?: () => Promise<TaskTemplate[]>;
  loadTask?: (taskId: string) => Promise<TaskTemplate>;
};

const COURSE_ID = "computer-networks";
const USER_ID = "student-demo";

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `evt-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

async function recordTaskOpened(task: TaskTemplate): Promise<void> {
  try {
    await recordEvent({
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
}: Props) {
  const [tasks, setTasks] = useState<TaskTemplate[]>([]);
  const [selected, setSelected] = useState<TaskTemplate | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

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

  async function selectTask(taskId: string) {
    setError("");
    try {
      const detail = await loadTask(taskId);
      setSelected(detail);
      void recordTaskOpened(detail);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "任务加载失败。");
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
            <TaskDetail task={selected} />
          ) : (
            <div className="empty-state">正在读取任务详情…</div>
          )}
        </div>
      </div>
    </section>
  );
}

function TaskDetail({ task }: { task: TaskTemplate }) {
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
        <DetailList title="关联知识点" items={task.knowledge_point_ids} />
        <DetailList title="关联资料" items={task.resource_ids} />
        <DetailList title="完成判据" items={task.completion_criteria} />
        <DetailList title="AI 反馈介入点" items={task.ai_feedback_points} />
      </div>

      <div className="task-detail__footer">
        <span>准备好开始这项学习任务了吗？</span>
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
