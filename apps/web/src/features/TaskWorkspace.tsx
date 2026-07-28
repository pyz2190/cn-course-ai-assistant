import { useEffect, useState } from "react";

import { getTask, listTasks } from "../api/client";
import type { TaskTemplate } from "../api/types";

const taskTypeLabels: Record<string, string> = {
  foundation: "基础学习",
  protocol_analysis: "协议分析与仿真",
  case_study: "案例分析",
  innovation_challenge: "创新挑战",
  project_practice: "项目实践",
  troubleshooting: "排错",
};

type Props = {
  loadTasks?: () => Promise<TaskTemplate[]>;
  loadTask?: (taskId: string) => Promise<TaskTemplate>;
};

export function TaskWorkspace({
  loadTasks = listTasks,
  loadTask = getTask,
}: Props) {
  const [tasks, setTasks] = useState<TaskTemplate[]>([]);
  const [selected, setSelected] = useState<TaskTemplate | null>(null);
  const [error, setError] = useState("");

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
      });
    return () => {
      active = false;
    };
  }, [loadTask, loadTasks]);

  async function selectTask(taskId: string) {
    setError("");
    try {
      setSelected(await loadTask(taskId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "任务加载失败。");
    }
  }

  return (
    <section className="panel tasks-panel" aria-labelledby="tasks-title">
      <div className="panel__heading">
        <div>
          <span className="eyebrow">任务引擎骨架</span>
          <h2 id="tasks-title">六类教学任务</h2>
        </div>
        <span className="badge badge--warm">{tasks.length || "…"}</span>
      </div>

      {error && <p className="error-message">{error}</p>}

      <div className="task-workspace">
        <div className="task-list" aria-label="任务列表">
          {tasks.map((task) => (
            <button
              key={task.task_id}
              type="button"
              className={`task-card ${
                selected?.task_id === task.task_id ? "task-card--selected" : ""
              }`}
              onClick={() => void selectTask(task.task_id)}
            >
              <span>{taskTypeLabels[task.task_type] ?? task.task_type}</span>
              <strong>{task.title}</strong>
            </button>
          ))}
        </div>

        <div className="task-detail">
          {selected ? (
            <>
              <span className="task-detail__type">
                {taskTypeLabels[selected.task_type] ?? selected.task_type}
              </span>
              <h3>{selected.title}</h3>
              <p>{selected.description}</p>
              <DetailList title="关联知识点" items={selected.knowledge_point_ids} />
              <DetailList title="关联资料" items={selected.resource_ids} />
              <DetailList title="完成判据" items={selected.completion_criteria} />
              <DetailList title="AI 反馈介入点" items={selected.ai_feedback_points} />
            </>
          ) : (
            <div className="empty-state">正在读取任务详情…</div>
          )}
        </div>
      </div>
    </section>
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
