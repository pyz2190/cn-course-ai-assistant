import { SystemStatus } from "./components/SystemStatus";
import { ChatPanel } from "./features/ChatPanel";
import { TaskWorkspace } from "./features/TaskWorkspace";
import "./styles.css";

export default function App() {
  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <span className="eyebrow">Computer Networks · AI Learning Studio</span>
          <h1>
            计算机网络
            <br />
            <em>AI 助教</em>
          </h1>
          <p>
            面向课程资料、可追溯问答与任务驱动学习的独立原型。
            当前骨架完全离线，不连接 Canvas 或真实模型服务。
          </p>
        </div>
        <div className="hero__status">
          <SystemStatus />
          <span className="hero__version">Skeleton v0.1</span>
        </div>
      </header>

      <div className="notice">
        <strong>开发基线</strong>
        <span>契约先行 · Mock 可替换 · 五人并行开发</span>
      </div>

      <div className="workspace-grid">
        <ChatPanel />
        <TaskWorkspace />
      </div>
    </main>
  );
}
