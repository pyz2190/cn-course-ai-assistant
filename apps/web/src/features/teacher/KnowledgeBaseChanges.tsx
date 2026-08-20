import { useCallback, useEffect, useState } from "react";

import { listKnowledgeBaseChanges, updateKnowledgeBaseChange } from "../../api/client";
import type { KnowledgeBaseChangeTask } from "../../api/types";

type ChangeStatus = KnowledgeBaseChangeTask["status"];

const STATUS_LABELS: Record<ChangeStatus, string> = {
  pending: "待处理",
  in_progress: "处理中",
  done: "已完成",
  wont_fix: "不予处理",
};

const OPEN_STATUSES: ChangeStatus[] = ["pending", "in_progress"];

const DEFAULT_HANDLER = "助教-demo";

export function KnowledgeBaseChanges() {
  const [items, setItems] = useState<KnowledgeBaseChangeTask[]>([]);
  const [filter, setFilter] = useState<"open" | "all">("open");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [handlingId, setHandlingId] = useState<string | null>(null);
  const [handler, setHandler] = useState(DEFAULT_HANDLER);
  const [notes, setNotes] = useState("");
  const [resourceIds, setResourceIds] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(() => {
    return listKnowledgeBaseChanges()
      .then((result) => {
        setError("");
        setItems(result);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "知识库变更加载失败。");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const refresh = useCallback(() => {
    setLoading(true);
    void load();
  }, [load]);

  useEffect(() => {
    void load();
  }, [load]);

  function startHandling(item: KnowledgeBaseChangeTask) {
    setHandlingId(item.change_id);
    setHandler(item.handler || DEFAULT_HANDLER);
    setNotes(item.resolution_notes ?? "");
    setResourceIds((item.resource_ids ?? []).join(", "));
    setError("");
  }

  async function submitUpdate(changeId: string, status: ChangeStatus) {
    if (status === "wont_fix" && !notes.trim()) {
      setError("不予处理需要填写处理说明。");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await updateKnowledgeBaseChange(changeId, {
        status,
        handler: handler.trim() || DEFAULT_HANDLER,
        resolution_notes: notes.trim(),
        resource_ids: resourceIds
          .split(",")
          .map((id) => id.trim())
          .filter(Boolean),
      });
      setHandlingId(null);
      setNotes("");
      setResourceIds("");
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "变更任务更新失败。");
    } finally {
      setSubmitting(false);
    }
  }

  const visible = filter === "all" ? items : items.filter((i) => OPEN_STATUSES.includes(i.status));
  const openCount = items.filter((i) => OPEN_STATUSES.includes(i.status)).length;

  return (
    <div className="teacher-section">
      <div className="teacher-section__head">
        <div>
          <span className="eyebrow">知识库优化</span>
          <h3>知识库变更任务</h3>
          <p className="teacher-section__desc">
            审核通过的回答反馈会生成知识库变更任务；处理完成后在此关闭，形成优化闭环。
          </p>
        </div>
        <div className="teacher-section__actions">
          <div className="segmented" role="group" aria-label="变更任务筛选">
            <button
              type="button"
              className={filter === "open" ? "segmented__active" : ""}
              onClick={() => setFilter("open")}
            >
              未关闭 {openCount > 0 && <span className="segmented__count">{openCount}</span>}
            </button>
            <button
              type="button"
              className={filter === "all" ? "segmented__active" : ""}
              onClick={() => setFilter("all")}
            >
              全部
            </button>
          </div>
          <button type="button" className="ghost-button" onClick={() => void refresh()}>
            刷新
          </button>
        </div>
      </div>

      {error && <p className="error-message">{error}</p>}

      {loading ? (
        <div className="empty-state">正在加载变更任务…</div>
      ) : visible.length === 0 ? (
        <div className="empty-state">
          {filter === "open" ? "没有未关闭的变更任务。" : "暂无知识库变更任务。"}
        </div>
      ) : (
        <ul className="kb-list">
          {visible.map((item) => (
            <li key={item.change_id} className="kb-card">
              <div className="kb-card__head">
                <span className={`kb-status kb-status--${item.status}`}>
                  {STATUS_LABELS[item.status]}
                </span>
                <span className="kb-card__meta">
                  {new Date(item.created_at).toLocaleString("zh-CN")}
                </span>
              </div>
              <p className="kb-card__question">
                <strong>问题：</strong>
                {item.question}
              </p>
              <p className="kb-card__reason">
                <strong>反馈原因：</strong>
                {item.reason}
              </p>
              {item.suggested_action && (
                <p className="kb-card__action">
                  <strong>建议动作：</strong>
                  {item.suggested_action}
                </p>
              )}

              {item.handler && (
                <p className="kb-card__handled">
                  由 {item.handler} 处理
                  {item.updated_at && ` · ${new Date(item.updated_at).toLocaleString("zh-CN")}`}
                  {item.resolution_notes && ` · ${item.resolution_notes}`}
                  {item.resource_ids && item.resource_ids.length > 0 && (
                    <span className="kb-card__resources">
                      {" "}
                      · 关联资料 {item.resource_ids.join("、")}
                    </span>
                  )}
                </p>
              )}

              {OPEN_STATUSES.includes(item.status) &&
                (handlingId === item.change_id ? (
                  <div className="review-form">
                    <label>
                      处理人
                      <input
                        value={handler}
                        onChange={(event) => setHandler(event.target.value)}
                      />
                    </label>
                    <label>
                      处理说明（不予处理时必填）
                      <textarea
                        value={notes}
                        onChange={(event) => setNotes(event.target.value)}
                        placeholder="记录本次如何优化知识库…"
                      />
                    </label>
                    <label>
                      关联资料 ID（逗号分隔，选填）
                      <input
                        value={resourceIds}
                        onChange={(event) => setResourceIds(event.target.value)}
                        placeholder="例如：resource-cn-textbook-001"
                      />
                    </label>
                    <div className="review-form__actions">
                      {item.status === "pending" && (
                        <button
                          type="button"
                          className="ghost-button"
                          disabled={submitting}
                          onClick={() => void submitUpdate(item.change_id, "in_progress")}
                        >
                          开始处理
                        </button>
                      )}
                      <button
                        type="button"
                        className="button-primary"
                        disabled={submitting}
                        onClick={() => void submitUpdate(item.change_id, "done")}
                      >
                        标记完成
                      </button>
                      <button
                        type="button"
                        className="button-danger"
                        disabled={submitting}
                        onClick={() => void submitUpdate(item.change_id, "wont_fix")}
                      >
                        不予处理
                      </button>
                      <button
                        type="button"
                        className="ghost-button"
                        disabled={submitting}
                        onClick={() => setHandlingId(null)}
                      >
                        取消
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    type="button"
                    className="button-primary"
                    onClick={() => startHandling(item)}
                  >
                    处理
                  </button>
                ))}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
