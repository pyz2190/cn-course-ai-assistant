import { useCallback, useEffect, useState } from "react";

import { listKnowledgeBaseChanges } from "../../api/client";
import type { KnowledgeBaseChangeTask } from "../../api/types";

export function KnowledgeBaseChanges() {
  const [items, setItems] = useState<KnowledgeBaseChangeTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    return listKnowledgeBaseChanges()
      .then((items) => {
        setError("");
        setItems(items);
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

  return (
    <div className="teacher-section">
      <div className="teacher-section__head">
        <div>
          <span className="eyebrow">知识库优化</span>
          <h3>知识库变更任务</h3>
          <p className="teacher-section__desc">
            审核通过的回答反馈会生成知识库变更任务，供持续优化课程知识库。
          </p>
        </div>
        <button type="button" className="ghost-button" onClick={() => void refresh()}>
          刷新
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {loading ? (
        <div className="empty-state">正在加载变更任务…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">暂无知识库变更任务。</div>
      ) : (
        <ul className="kb-list">
          {items.map((item) => (
            <li key={item.change_id} className="kb-card">
              <div className="kb-card__head">
                <span className="kb-status">待处理</span>
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
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
