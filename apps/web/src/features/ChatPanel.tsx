import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { askQuestion, createFeedback, recordEvent } from "../api/client";
import type {
  AnswerFeedback,
  AnswerFeedbackCreate,
  AskRequest,
  AskResponse,
  LearningEvent,
} from "../api/types";
import {
  CitationList,
  parseAnswerSegments,
} from "../components/CitationList";

type Props = {
  ask?: (request: AskRequest) => Promise<AskResponse>;
  createAnswerFeedback?: (request: AnswerFeedbackCreate) => Promise<AnswerFeedback>;
  recordLearningEvent?: (event: LearningEvent) => Promise<LearningEvent>;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  question?: string;
  response?: AskResponse;
};

const SUGGESTED_QUESTIONS = [
  "TCP 为什么需要三次握手？",
  "DNS 是如何进行域名解析的？",
  "TCP 拥塞控制有哪些阶段？",
  "UDP 和 TCP 有什么区别？",
  "IPv4 地址是如何划分的？",
];

const COURSE_ID = "computer-networks";
const USER_ID = "student-demo";

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/** 尽力而为地记录学习行为事件，失败不影响问答主流程。 */
async function recordQaEvent(
  question: string,
  response: AskResponse,
  saveEvent: (event: LearningEvent) => Promise<LearningEvent>,
): Promise<void> {
  try {
    await saveEvent({
      course_id: COURSE_ID,
      user_id: USER_ID,
      event_id: newId(),
      event_type: "qa_asked",
      object_id: response.request_id,
      occurred_at: new Date().toISOString(),
      payload: { question, confidence: response.confidence },
    });
  } catch {
    // 事件记录失败静默忽略，保持问答可用。
  }
}

export function ChatPanel({
  ask = askQuestion,
  createAnswerFeedback = createFeedback,
  recordLearningEvent = recordEvent,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "你好，我是《计算机网络》AI 助教。你可以就课程内容向我提问，我会基于课程资料作答并给出可追溯的引用来源。",
    },
  ]);
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [highlighted, setHighlighted] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    if (typeof el.scrollTo === "function") {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    } else {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, submitting]);

  async function submit(question: string) {
    const trimmed = question.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    setError("");
    setHighlighted(null);
    setMessages((prev) => [...prev, { id: newId(), role: "user", text: trimmed }]);
    try {
      const response = await ask({
        course_id: COURSE_ID,
        user_id: USER_ID,
        question: trimmed,
      });
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          text: response.answer,
          question: trimmed,
          response,
        },
      ]);
      void recordQaEvent(trimmed, response, recordLearningEvent);
    } catch (caught) {
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          text: caught instanceof Error ? caught.message : "问答服务暂时不可用。",
        },
      ]);
    } finally {
      setSubmitting(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submit(input);
    setInput("");
  }

  return (
    <section className="panel chat-panel" aria-labelledby="chat-title">
      <div className="panel__heading">
        <div>
          <span className="eyebrow">RAG 课程问答</span>
          <h2 id="chat-title">现在就问问课程内容</h2>
        </div>
      </div>

      <div className="chat-capabilities" aria-label="问答能力">
        <span>Qdrant 检索</span>
        <span>按句引用</span>
        <span>课程资料优先</span>
      </div>

      <div className="suggestions" aria-label="建议问题">
        {SUGGESTED_QUESTIONS.map((question) => (
          <button
            key={question}
            type="button"
            className="suggestion-chip"
            disabled={submitting}
            onClick={() => void submit(question)}
          >
            {question}
          </button>
        ))}
      </div>

      <div className="chat-log" ref={scrollRef} aria-live="polite">
        {messages.map((message) =>
          message.role === "user" ? (
            <div key={message.id} className="chat-message chat-message--user">
              <div className="bubble">{message.text}</div>
            </div>
          ) : message.response ? (
            <AnswerBubble
              key={message.id}
              message={message}
              highlighted={highlighted}
              onSelectMarker={setHighlighted}
              createAnswerFeedback={createAnswerFeedback}
              recordLearningEvent={recordLearningEvent}
            />
          ) : (
            <div key={message.id} className="chat-message chat-message--assistant">
              <div
                className={`bubble${message.id === "welcome" ? " bubble--welcome" : " bubble--error"}`}
              >
                {message.text}
              </div>
            </div>
          ),
        )}
        {submitting && (
          <div className="chat-message chat-message--assistant">
            <div className="bubble bubble--thinking">正在检索课程资料…</div>
          </div>
        )}
      </div>

      {error && <p className="error-message">{error}</p>}

      <form onSubmit={handleSubmit} className="question-form">
        <label htmlFor="question">向 AI 助教提问</label>
        <div className="question-form__row">
          <input
            id="question"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="输入课程相关问题，回车发送…"
            disabled={submitting}
          />
          <button type="submit" disabled={submitting || !input.trim()}>
            {submitting ? "检索中…" : "发送"}
          </button>
        </div>
      </form>
    </section>
  );
}

function AnswerBubble({
  message,
  highlighted,
  onSelectMarker,
  createAnswerFeedback,
  recordLearningEvent,
}: {
  message: Message;
  highlighted: number | null;
  onSelectMarker: (number: number | null) => void;
  createAnswerFeedback: (request: AnswerFeedbackCreate) => Promise<AnswerFeedback>;
  recordLearningEvent: (event: LearningEvent) => Promise<LearningEvent>;
}) {
  const response = message.response!;
  const segments = parseAnswerSegments(response.answer);
  const hasMarkers = segments.some((segment) => segment.kind === "marker");
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackReason, setFeedbackReason] = useState("");
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedbackError, setFeedbackError] = useState("");

  async function submitFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const reason = feedbackReason.trim();
    if (!reason || feedbackSubmitting || feedbackSubmitted) return;

    setFeedbackSubmitting(true);
    setFeedbackError("");
    try {
      const feedback = await createAnswerFeedback({
        course_id: COURSE_ID,
        user_id: USER_ID,
        request_id: response.request_id,
        question: message.question ?? "",
        answer: response.answer,
        reason,
        citation_ids: response.citations.map((citation) => citation.citation_id),
      });
      setFeedbackSubmitted(true);
      try {
        await recordLearningEvent({
          course_id: COURSE_ID,
          user_id: USER_ID,
          event_id: newId(),
          event_type: "feedback_submitted",
          object_id: feedback.feedback_id,
          occurred_at: new Date().toISOString(),
          payload: { request_id: response.request_id },
        });
      } catch {
        setFeedbackError("反馈已提交审核，但学习事件记录失败。");
      }
    } catch (caught) {
      setFeedbackError(
        caught instanceof Error ? caught.message : "反馈提交失败，请重试。",
      );
    } finally {
      setFeedbackSubmitting(false);
    }
  }

  return (
    <div className="chat-message chat-message--assistant">
      <div className="bubble bubble--answer">
        <p className="answer__text">
          {segments.map((segment, index) =>
            segment.kind === "marker" ? (
              <button
                key={`${index}-${segment.number}`}
                type="button"
                className={`citation-marker${
                  highlighted === segment.number ? " citation-marker--active" : ""
                }`}
                onClick={() =>
                  onSelectMarker(highlighted === segment.number ? null : segment.number)
                }
                aria-label={`跳转到引用 ${segment.number}`}
              >
                [{segment.number}]
              </button>
            ) : (
              <span key={index}>{segment.text}</span>
            ),
          )}
        </p>

        <div className="answer__meta">
          <span>
            置信度 {Math.round(response.confidence * 100)}%
            {response.mode === "external" ? " · 外部模型" : " · 离线检索"}
            {response.degraded ? " · 已降级" : ""}
          </span>
          <span>request: {response.request_id.slice(0, 8)}</span>
        </div>

        {!hasMarkers && response.citations.length > 0 && (
          <span className="answer__hint">以下来源支持本次回答：</span>
        )}

        <CitationList
          citations={response.citations}
          highlighted={highlighted}
          onSelect={(citationId) => {
            if (citationId == null) {
              onSelectMarker(null);
            }
          }}
        />

        <div className="answer-feedback">
          {feedbackSubmitted ? (
            <span className="answer-feedback__submitted">已提交审核</span>
          ) : (
            <button
              type="button"
              className="answer-feedback__trigger"
              onClick={() => {
                setFeedbackOpen((open) => !open);
                setFeedbackError("");
              }}
              aria-expanded={feedbackOpen}
            >
              回答无效
            </button>
          )}

          {feedbackOpen && !feedbackSubmitted && (
            <form className="answer-feedback__form" onSubmit={submitFeedback}>
              <label htmlFor={`feedback-reason-${message.id}`}>请说明回答存在的问题</label>
              <textarea
                id={`feedback-reason-${message.id}`}
                value={feedbackReason}
                onChange={(event) => setFeedbackReason(event.target.value)}
                disabled={feedbackSubmitting}
                rows={3}
              />
              <button
                type="submit"
                disabled={feedbackSubmitting || !feedbackReason.trim()}
              >
                {feedbackSubmitting ? "正在提交…" : "提交反馈"}
              </button>
            </form>
          )}

          {feedbackError && <p className="answer-feedback__error">{feedbackError}</p>}
        </div>
      </div>
    </div>
  );
}
