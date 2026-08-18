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
            默认离线运行：Qdrant 向量检索 + 确定性离线生成，不连接 Canvas 或外部模型。
          </p>
        </div>
        <div className="hero__status">
          <SystemStatus />
          <span className="hero__version">Demo v0.2</span>
        </div>
      </header>

      <div className="notice">
        <strong>离线 RAG</strong>
        <span>Qdrant 检索 · 按句引用 · 六类任务 · 完全独立</span>
      </div>

      <div className="workspace-grid">
        <ChatPanel />
        <TaskWorkspace />
      </div>
    </main>
  );
}
