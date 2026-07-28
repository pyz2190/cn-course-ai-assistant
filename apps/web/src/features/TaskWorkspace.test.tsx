import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { TaskTemplate } from "../api/types";
import { TaskWorkspace } from "./TaskWorkspace";

const task: TaskTemplate = {
  task_id: "task-protocol-tcp-handshake",
  title: "Wireshark 分析 TCP 三次握手",
  description: "从抓包中定位三类报文。",
  task_type: "protocol_analysis",
  knowledge_point_ids: ["kp-transport-tcp-handshake"],
  resource_ids: ["resource-cn-textbook-001"],
  prerequisite_ids: [],
  completion_criteria: ["解释序列号变化。"],
  ai_feedback_points: ["检查握手顺序。"],
  status: "published",
};

const troubleshootingTask: TaskTemplate = {
  ...task,
  task_id: "task-troubleshooting-dns",
  title: "DNS 解析故障诊断",
  description: "根据日志定位域名解析失败原因。",
  task_type: "troubleshooting",
  knowledge_point_ids: ["kp-application-dns"],
  resource_ids: ["resource-dns-lab-001"],
  completion_criteria: ["给出故障定位步骤。"],
  ai_feedback_points: ["检查排查顺序。"],
};

describe("TaskWorkspace", () => {
  it("loads and shows task details", async () => {
    render(
      <TaskWorkspace
        loadTasks={vi.fn().mockResolvedValue([task])}
        loadTask={vi.fn().mockResolvedValue(task)}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Wireshark 分析 TCP 三次握手" }),
    ).toBeInTheDocument();
    expect(screen.getByText("resource-cn-textbook-001")).toBeInTheDocument();
    expect(screen.getByText("解释序列号变化。")).toBeInTheDocument();
    expect(screen.getByText("检查握手顺序。")).toBeInTheDocument();
  });

  it("switches between task details", async () => {
    const user = userEvent.setup();
    const loadTask = vi.fn((taskId: string) =>
      Promise.resolve(taskId === troubleshootingTask.task_id ? troubleshootingTask : task),
    );

    render(
      <TaskWorkspace
        loadTasks={vi.fn().mockResolvedValue([task, troubleshootingTask])}
        loadTask={loadTask}
      />,
    );

    await screen.findByRole("heading", { name: task.title });
    await user.click(screen.getByRole("button", { name: /DNS 解析故障诊断/ }));

    expect(
      await screen.findByRole("heading", { name: troubleshootingTask.title }),
    ).toBeInTheDocument();
    expect(screen.getByText("resource-dns-lab-001")).toBeInTheDocument();
  });
});
