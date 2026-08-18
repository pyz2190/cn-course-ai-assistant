import { useState } from "react";

import { EventQuery } from "./EventQuery";
import { FeedbackReview } from "./FeedbackReview";
import { KnowledgeBaseChanges } from "./KnowledgeBaseChanges";
import { ResourceUpload } from "./ResourceUpload";

type Tab = "feedback" | "kb" | "upload" | "events";

const TABS: { key: Tab; label: string }[] = [
  { key: "feedback", label: "反馈审核" },
  { key: "kb", label: "知识库变更" },
  { key: "upload", label: "资料上传" },
  { key: "events", label: "学习行为" },
];

export function TeacherDashboard() {
  const [tab, setTab] = useState<Tab>("feedback");

  return (
    <section className="panel teacher-dashboard" aria-label="教师管理界面">
      <div className="panel__heading">
        <div>
          <span className="eyebrow">教师 / 助教工作台</span>
          <h2>课程管理</h2>
        </div>
        <span className="badge badge--warm">教师侧</span>
      </div>

      <nav className="teacher-tabs" aria-label="管理功能切换">
        {TABS.map((item) => (
          <button
            key={item.key}
            type="button"
            className={tab === item.key ? "teacher-tabs__active" : ""}
            onClick={() => setTab(item.key)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {tab === "feedback" && <FeedbackReview />}
      {tab === "kb" && <KnowledgeBaseChanges />}
      {tab === "upload" && <ResourceUpload />}
      {tab === "events" && <EventQuery />}
    </section>
  );
}
