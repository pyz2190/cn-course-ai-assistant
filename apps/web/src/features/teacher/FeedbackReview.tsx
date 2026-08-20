import { useCallback, useEffect, useState } from "react";

import { listFeedback, reviewFeedback } from "../../api/client";
import type { AnswerFeedback } from "../../api/types";

const STATUS_LABELS: Record<AnswerFeedback["status"], string> = {
  pending_review: "待审核",
  approved: "已通过",
  rejected: "已驳回",
};

const DEFAULT_REVIEWER = "助教-demo";

export function FeedbackReview() {
  const [items, setItems] = useState<AnswerFeedback[]>([]);
  const [filter, setFilter] = useState<"pending_review" | "all">("pending_review");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [reviewingId, setReviewingId] = useState<string | null>(null);
  const [reviewer, setReviewer] = useState(DEFAULT_REVIEWER);
  const [notes, setNotes] = useState("");
  const [suggestedAction, setSuggestedAction] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(() => {
    return listFeedback(filter === "all" ? {} : { status: "pending_review" })
      .then((result) => {
        setError("");
        setItems(result);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "反馈列表加载失败。");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [filter]);

  const refresh = useCallback(() => {
    setLoading(true);
    void load();
  }, [load]);

  useEffect(() => {
    void load();
  }, [load]);

  async function submitReview(feedbackId: string, decision: "approved" | "rejected") {
    setSubmitting(true);
    setError("");
    try {
      await reviewFeedback(feedbackId, {
        decision,
        reviewer: reviewer.trim() || DEFAULT_REVIEWER,
        review_notes: notes.trim(),
        suggested_action: suggestedAction.trim() || null,
      });
      setReviewingId(null);
      setNotes("");
      setSuggestedAction("");
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "审核提交失败。");
    } finally {
      setSubmitting(false);
    }
  }

  const pendingCount = items.filter((item) => item.status === "pending_review").length;

  return (
    <div className="teacher-section">
      <div className="teacher-section__head">
        <div>
          <span className="eyebrow">反馈审核</span>
          <h3>无效回答审核</h3>
          <p className="teacher-section__desc">
            学生标记为无效的回答进入此处审核；审核通过后自动生成知识库变更任务。
          </p>
        </div>
        <div className="teacher-section__actions">
          <div className="segmented">
            <button
              type="button"
              className={filter === "pending_review" ? "segmented__active" : ""}
              onClick={() => setFilter("pending_review")}
            >
              待审核 {pendingCount > 0 && <span className="segmented__count">{pendingCount}</span>}
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
        <div className="empty-state">正在加载反馈…</div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          {filter === "pending_review" ? "没有待审核的反馈。" : "暂无反馈记录。"}
        </div>
      ) : (
        <ul className="feedback-list">
          {items.map((item) => (
            <li key={item.feedback_id} className="feedback-card">
              <div className="feedback-card__head">
                <span className={`feedback-status feedback-status--${item.status}`}>
                  {STATUS_LABELS[item.status]}
                </span>
                <span className="feedback-card__meta">
                  {item.user_id} · {new Date(item.created_at).toLocaleString("zh-CN")}
                </span>
              </div>

              <p className="feedback-card__question">
                <strong>问题：</strong>
                {item.question}
              </p>
              <p className="feedback-card__reason">
                <strong>反馈原因：</strong>
                {item.reason}
              </p>

              {item.reviewed_at && (
                <p className="feedback-card__reviewed">
                  已由 {item.reviewer} 审核于{" "}
                  {new Date(item.reviewed_at).toLocaleString("zh-CN")}
                  {item.knowledge_base_change_id && (
                    <span className="feedback-card__kb"> · 已生成知识库变更</span>
                  )}
                </p>
              )}

              {item.status === "pending_review" &&
                (reviewingId === item.feedback_id ? (
                  <div className="review-form">
                    <label>
                      审核人
                      <input
                        value={reviewer}
                        onChange={(event) => setReviewer(event.target.value)}
                      />
                    </label>
                    <label>
                      审核意见
                      <textarea
                        value={notes}
                        onChange={(event) => setNotes(event.target.value)}
                        placeholder="记录审核结论或补充说明…"
                      />
                    </label>
                    <label>
                      建议动作（通过时用于生成知识库变更任务）
                      <input
                        value={suggestedAction}
                        onChange={(event) => setSuggestedAction(event.target.value)}
                        placeholder="例如：补充 TCP 三次握手的序列号解释"
                      />
                    </label>
                    <div className="review-form__actions">
                      <button
                        type="button"
                        className="button-primary"
                        disabled={submitting}
                        onClick={() => void submitReview(item.feedback_id, "approved")}
                      >
                        通过并生成变更
                      </button>
                      <button
                        type="button"
                        className="button-danger"
                        disabled={submitting}
                        onClick={() => void submitReview(item.feedback_id, "rejected")}
                      >
                        驳回
                      </button>
                      <button
                        type="button"
                        className="ghost-button"
                        disabled={submitting}
                        onClick={() => setReviewingId(null)}
                      >
                        取消
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    type="button"
                    className="button-primary"
                    onClick={() => setReviewingId(item.feedback_id)}
                  >
                    审核
                  </button>
                ))}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
