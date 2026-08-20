import { useState } from "react";

import { ChatPanel } from "./features/ChatPanel";
import { TaskWorkspace } from "./features/TaskWorkspace";
import { TeacherDashboard } from "./features/teacher/TeacherDashboard";
import "./styles.css";

type View = "student" | "teacher";

export default function App() {
  const [view, setView] = useState<View>("student");
  const isStudent = view === "student";

  return (
    <main className="app-shell">
      <section className="hero-screen" aria-labelledby="app-title">
        <header className="topbar">
          <span className="eyebrow">Computer Networks · AI Learning Studio</span>

          <nav className="view-switcher" aria-label="视图切换">
            <button
              type="button"
              className={isStudent ? "view-switcher__active" : ""}
              aria-pressed={isStudent}
              onClick={() => setView("student")}
            >
              学生视图
            </button>
            <button
              type="button"
              className={isStudent ? "" : "view-switcher__active"}
              aria-pressed={!isStudent}
              onClick={() => setView("teacher")}
            >
              教师 / 助教视图
            </button>
          </nav>

          <span className="hero__version">Demo v0.2</span>
        </header>

        {isStudent ? (
          <>
            <div className="hero-content">
              <h1 id="app-title">
                计算机网络 <em>AI 助教</em>
              </h1>
              <ChatPanel />
            </div>

            <a className="scroll-cue" href="#tasks">
              <span aria-hidden="true">↓</span> 探索六类教学任务
            </a>
          </>
        ) : (
          <div className="hero-content hero-content--teacher">
            <h1 id="app-title">
              计算机网络 <em>AI 助教</em>
            </h1>
            <TeacherDashboard />
          </div>
        )}
      </section>

      {isStudent && (
        <section className="tasks-section" id="tasks">
          <TaskWorkspace />
        </section>
      )}
    </main>
  );
}
