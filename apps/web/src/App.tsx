import { ChatPanel } from "./features/ChatPanel";
import { TaskWorkspace } from "./features/TaskWorkspace";
import "./styles.css";

export default function App() {
  return (
    <main className="app-shell">
      <section className="hero-screen" aria-labelledby="app-title">
        <header className="topbar">
          <span className="eyebrow">Computer Networks · AI Learning Studio</span>
          <span className="hero__version">Demo v0.2</span>
        </header>

        <div className="hero-content">
          <h1 id="app-title">计算机网络 <em>AI 助教</em></h1>
          <ChatPanel />
        </div>

        <a className="scroll-cue" href="#tasks">
          <span aria-hidden="true">↓</span> 探索六类教学任务
        </a>
      </section>

      <section className="tasks-section" id="tasks">
        <TaskWorkspace />
      </section>
    </main>
  );
}
