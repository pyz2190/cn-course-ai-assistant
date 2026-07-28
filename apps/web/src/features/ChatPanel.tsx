import { useState } from "react";
import type { FormEvent } from "react";

import { askQuestion } from "../api/client";
import type { AskRequest, AskResponse } from "../api/types";
import { CitationList } from "../components/CitationList";

type Props = {
  ask?: (request: AskRequest) => Promise<AskResponse>;
};

export function ChatPanel({ ask = askQuestion }: Props) {
  const [question, setQuestion] = useState("TCP 为什么需要三次握手？");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) {
      setError("请输入问题。");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      setAnswer(
        await ask({
          course_id: "computer-networks",
          user_id: "student-demo",
          question: question.trim(),
        }),
      );
    } catch (caught) {
      setAnswer(null);
      setError(caught instanceof Error ? caught.message : "问答服务暂时不可用。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="panel chat-panel" aria-labelledby="chat-title">
      <div className="panel__heading">
        <div>
          <span className="eyebrow">RAG 问答骨架</span>
          <h2 id="chat-title">带引用的课程问答</h2>
        </div>
        <span className="badge">Mock</span>
      </div>

      <form onSubmit={handleSubmit} className="question-form">
        <label htmlFor="question">向 AI 助教提问</label>
        <div className="question-form__row">
          <input
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="例如：TCP 为什么需要三次握手？"
          />
          <button type="submit" disabled={submitting}>
            {submitting ? "检索中…" : "提问"}
          </button>
        </div>
      </form>

      {error && <p className="error-message">{error}</p>}

      {answer ? (
        <div className="answer">
          <div className="answer__meta">
            <span>模拟回答</span>
            <span>置信度 {Math.round(answer.confidence * 100)}%</span>
          </div>
          <p className="answer__text">{answer.answer}</p>
          <CitationList citations={answer.citations} />
        </div>
      ) : (
        <div className="empty-state">
          提交问题后，这里会展示回答、置信度和可追溯引用。
        </div>
      )}
    </section>
  );
}
