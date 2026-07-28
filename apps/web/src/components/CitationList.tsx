import type { AskResponse } from "../api/types";

type Citation = AskResponse["citations"][number];

export function CitationList({ citations }: { citations: Citation[] }) {
  return (
    <ol className="citations" aria-label="回答引用">
      {citations.map((citation, index) => {
        const pageRange =
          citation.page_start === null || citation.page_start === undefined
            ? "页码未标注"
            : `第 ${citation.page_start}${
                citation.page_end && citation.page_end !== citation.page_start
                  ? `–${citation.page_end}`
                  : ""
              } 页`;
        return (
          <li key={citation.citation_id} className="citation">
            <span className="citation__index">[{index + 1}]</span>
            <div>
              <strong>{citation.title}</strong>
              <span>
                {citation.chapter} · {pageRange}
              </span>
              <p>{citation.quote}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
