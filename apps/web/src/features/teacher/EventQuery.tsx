import { useCallback, useEffect, useState } from "react";

import { queryEvents } from "../../api/client";
import type { LearningEvent } from "../../api/types";

const EVENT_TYPE_LABELS: Record<string, string> = {
  qa_asked: "问答提问",
  task_opened: "打开任务",
  task_completed: "完成任务",
  feedback_submitted: "提交反馈",
};

export function EventQuery() {
  const [events, setEvents] = useState<LearningEvent[]>([]);
  const [courseId, setCourseId] = useState("");
  const [userId, setUserId] = useState("");
  const [eventType, setEventType] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    const params: Record<string, string> = {};
    if (courseId.trim()) params.course_id = courseId.trim();
    if (userId.trim()) params.user_id = userId.trim();
    if (eventType) params.event_type = eventType;
    return queryEvents(params)
      .then((result) => {
        setError("");
        setEvents(result);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "学习事件查询失败。");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [courseId, userId, eventType]);

  const refresh = useCallback(() => {
    setLoading(true);
    void load();
  }, [load]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="teacher-section">
      <div className="teacher-section__head">
        <div>
          <span className="eyebrow">学习分析</span>
          <h3>学习行为事件</h3>
          <p className="teacher-section__desc">
            查询独立系统记录的学习行为事件，用于学习分析与评测支撑。
          </p>
        </div>
      </div>

      <div className="event-filters">
        <input
          placeholder="课程 ID"
          value={courseId}
          onChange={(event) => setCourseId(event.target.value)}
        />
        <input
          placeholder="用户 ID"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
        />
        <select value={eventType} onChange={(event) => setEventType(event.target.value)}>
          <option value="">全部事件类型</option>
          {Object.entries(EVENT_TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <button type="button" className="ghost-button" onClick={() => void refresh()}>
          查询
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {loading ? (
        <div className="empty-state">正在查询事件…</div>
      ) : events.length === 0 ? (
        <div className="empty-state">没有匹配的学习事件。</div>
      ) : (
        <table className="event-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>事件类型</th>
              <th>用户</th>
              <th>对象</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.event_id}>
                <td>{new Date(event.occurred_at).toLocaleString("zh-CN")}</td>
                <td>{EVENT_TYPE_LABELS[event.event_type] ?? event.event_type}</td>
                <td>{event.user_id}</td>
                <td className="event-table__object">{event.object_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
