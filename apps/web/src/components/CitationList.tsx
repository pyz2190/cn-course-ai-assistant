import { useState } from "react";
import type { AskResponse } from "../api/types";

type Citation = AskResponse["citations"][number];

type Props = {
  citations: Citation[];
  /** 当前高亮的引用角标编号（1 起），用于行内角标点击联动 */
  highlighted?: number | null;
  /** 点击引用卡片时回调，用于反向联动 */
  onSelect?: (citationId: string | null) => void;
};

function pageRange(citation: Citation): string {
  if (citation.page_start == null) {
    return "页码未标注";
  }
  if (citation.page_end && citation.page_end !== citation.page_start) {
    return `第 ${citation.page_start}–${citation.page_end} 页`;
  }
  return `第 ${citation.page_start} 页`;
}

function scoreLabel(citation: Citation): string | null {
  const parts: string[] = [];
  if (citation.retrieval_score != null) {
    parts.push(`检索 ${citation.retrieval_score.toFixed(2)}`);
  }
  if (citation.rerank_score != null) {
    parts.push(`重排 ${citation.rerank_score.toFixed(2)}`);
  }
  return parts.length ? parts.join(" · ") : null;
}

export function CitationList({ citations, highlighted, onSelect }: Props) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  if (citations.length === 0) {
    return (
      <div className="citations-empty" role="status">
        本次回答未引用任何课程资料。
      </div>
    );
  }

  return (
    <ol className="citations" aria-label="回答引用">
      {citations.map((citation, index) => {
        const number = index + 1;
        const isHighlighted = highlighted === number;
        const isExpanded = expanded[citation.citation_id] ?? false;
        const score = scoreLabel(citation);
        return (
          <li
            key={citation.citation_id}
            id={`citation-${number}`}
            className={`citation${isHighlighted ? " citation--highlighted" : ""}`}
            onClick={() => onSelect?.(isHighlighted ? null : citation.citation_id)}
          >
            <span className="citation__index">[{number}]</span>
            <div className="citation__body">
              <div className="citation__head">
                <strong>{citation.title}</strong>
                {score && <span className="citation__score">{score}</span>}
              </div>
              <span className="citation__meta">
                {citation.chapter} · {pageRange(citation)}
              </span>
              <button
                type="button"
                className="citation__toggle"
                onClick={(event) => {
                  event.stopPropagation();
                  setExpanded((prev) => ({
                    ...prev,
                    [citation.citation_id]: !prev[citation.citation_id],
                  }));
                }}
              >
                {isExpanded ? "收起原文" : "查看原文"}
              </button>
              {isExpanded && <p className="citation__quote">{citation.quote}</p>}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

/** 把回答文本按 `[1]`、`[2]` 行内角标切分为文本片段与角标片段 */
export type AnswerSegment =
  | { kind: "text"; text: string }
  | { kind: "marker"; number: number };

export function parseAnswerSegments(answer: string): AnswerSegment[] {
  const segments: AnswerSegment[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(answer)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ kind: "text", text: answer.slice(lastIndex, match.index) });
    }
    segments.push({ kind: "marker", number: Number(match[1]) });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < answer.length) {
    segments.push({ kind: "text", text: answer.slice(lastIndex) });
  }
  return segments;
}
