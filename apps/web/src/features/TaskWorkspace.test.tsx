import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { KnowledgePoint, TaskTemplate } from "../api/types";
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

const handshakePoint: KnowledgePoint = {
  knowledge_point_id: "kp-transport-tcp-handshake",
  name: "TCP 三次握手",
  chapter: "第 3 章 运输层",
  parent_id: "kp-network-overview",
  kind: "protocol",
  difficulty: "intermediate",
  keywords_zh: ["三次握手"],
  keywords_en: ["three-way handshake"],
  prerequisite_ids: ["kp-transport-udp"],
  summary: "TCP 通过三次握手同步初始序列号。",
  review_status: "approved",
  maintainer: "course-team",
};

const udpPoint: KnowledgePoint = {
  ...handshakePoint,
  knowledge_point_id: "kp-transport-udp",
  name: "UDP 协议",
  prerequisite_ids: [],
};

describe("TaskWorkspace", () => {
  it("shows knowledge point names and prerequisites instead of raw ids", async () => {
    render(
      <TaskWorkspace
        loadTasks={vi.fn().mockResolvedValue([task])}
        loadTask={vi.fn().mockResolvedValue(task)}
        loadKnowledgePoints={vi.fn().mockResolvedValue([handshakePoint, udpPoint])}
      />,
    );

    expect(await screen.findByText("TCP 三次握手")).toBeInTheDocument();
    expect(screen.getByText("第 3 章 运输层")).toBeInTheDocument();
    expect(screen.getByText("先修：UDP 协议")).toBeInTheDocument();
    expect(screen.queryByText("kp-transport-tcp-handshake")).not.toBeInTheDocument();
  });

  it("falls back to the raw id when knowledge points cannot be loaded", async () => {
    render(
      <TaskWorkspace
        loadTasks={vi.fn().mockResolvedValue([task])}
        loadTask={vi.fn().mockResolvedValue(task)}
        loadKnowledgePoints={vi.fn().mockRejectedValue(new Error("离线"))}
      />,
    );

    expect(await screen.findByText("kp-transport-tcp-handshake")).toBeInTheDocument();
  });

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

  it("records task_completed once and disables the completion button", async () => {
    const user = userEvent.setup();
    const recordLearningEvent = vi.fn().mockImplementation((event) => Promise.resolve(event));

    render(
      <TaskWorkspace
        loadTasks={vi.fn().mockResolvedValue([task])}
        loadTask={vi.fn().mockResolvedValue(task)}
        recordLearningEvent={recordLearningEvent}
      />,
    );

    const completeButton = await screen.findByRole("button", { name: "标记完成" });
    await user.click(completeButton);

    expect(await screen.findByRole("button", { name: "已完成" })).toBeDisabled();
    expect(recordLearningEvent).toHaveBeenCalledTimes(1);
    expect(recordLearningEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        course_id: "computer-networks",
        user_id: "student-demo",
        event_type: "task_completed",
        object_id: task.task_id,
        payload: { task_type: task.task_type },
      }),
    );
  });

  it("shows a retryable error when task completion recording fails", async () => {
    const user = userEvent.setup();
    const recordLearningEvent = vi
      .fn()
      .mockRejectedValueOnce(new Error("事件服务暂时不可用。"))
      .mockImplementation((event) => Promise.resolve(event));

    render(
      <TaskWorkspace
        loadTasks={vi.fn().mockResolvedValue([task])}
        loadTask={vi.fn().mockResolvedValue(task)}
        recordLearningEvent={recordLearningEvent}
      />,
    );

    await user.click(await screen.findByRole("button", { name: "标记完成" }));
    expect(await screen.findByText("事件服务暂时不可用。")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "标记完成" }));
    expect(await screen.findByRole("button", { name: "已完成" })).toBeDisabled();
    expect(recordLearningEvent).toHaveBeenCalledTimes(2);
  });
});
