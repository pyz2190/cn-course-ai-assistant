import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ChatPanel } from "./ChatPanel";

const askResponse = {
  answer: "三次握手用于同步初始序列号。[1]",
  confidence: 0.92,
  request_id: "req-test",
  degraded: false,
  mode: "offline" as const,
  citations: [
    {
      citation_id: "citation-1",
      chunk_id: "chunk-1",
      resource_id: "resource-1",
      title: "计算机网络：自顶向下方法",
      chapter: "第 3 章 运输层",
      page_start: 214,
      page_end: 215,
      quote: "TCP 使用三次握手同步双方的初始序列号。",
      source_url: null,
    },
  ],
};

describe("ChatPanel", () => {
  it("renders an answer with an inline marker and a traceable citation", async () => {
    const user = userEvent.setup();
    const ask = vi.fn().mockResolvedValue(askResponse);

    render(<ChatPanel ask={ask} />);
    await user.type(
      screen.getByLabelText("向 AI 助教提问"),
      "TCP 为什么需要三次握手？",
    );
    await user.click(screen.getByRole("button", { name: "发送" }));

    expect(await screen.findByText("三次握手用于同步初始序列号。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "跳转到引用 1" })).toBeInTheDocument();
    expect(screen.getByText(/第 3 章 运输层/)).toBeInTheDocument();
    expect(screen.getByText(/第 214–215 页/)).toBeInTheDocument();
  });

  it("shows a readable service error", async () => {
    const user = userEvent.setup();
    render(
      <ChatPanel ask={vi.fn().mockRejectedValue(new Error("问答服务暂时不可用。"))} />,
    );

    await user.type(screen.getByLabelText("向 AI 助教提问"), "测试问题");
    await user.click(screen.getByRole("button", { name: "发送" }));

    expect(await screen.findByText("问答服务暂时不可用。")).toBeInTheDocument();
  });

  it("submits invalid-answer feedback and records feedback_submitted", async () => {
    const user = userEvent.setup();
    const createAnswerFeedback = vi.fn().mockResolvedValue({
      feedback_id: "feedback-test",
      course_id: "computer-networks",
      user_id: "student-demo",
      request_id: "req-test",
      question: "TCP 为什么需要三次握手？",
      answer: askResponse.answer,
      reason: "没有解释初始序列号。",
      citation_ids: ["citation-1"],
      status: "pending_review",
      created_at: "2026-08-18T09:00:00Z",
      reviewer: null,
      reviewed_at: null,
      review_notes: "",
      knowledge_base_change_id: null,
    });
    const recordLearningEvent = vi.fn().mockImplementation((event) => Promise.resolve(event));

    render(
      <ChatPanel
        ask={vi.fn().mockResolvedValue(askResponse)}
        createAnswerFeedback={createAnswerFeedback}
        recordLearningEvent={recordLearningEvent}
      />,
    );

    await user.type(
      screen.getByLabelText("向 AI 助教提问"),
      "TCP 为什么需要三次握手？",
    );
    await user.click(screen.getByRole("button", { name: "发送" }));
    await user.click(await screen.findByRole("button", { name: "回答无效" }));
    await user.type(
      screen.getByLabelText("请说明回答存在的问题"),
      "没有解释初始序列号。",
    );
    await user.click(screen.getByRole("button", { name: "提交反馈" }));

    expect(await screen.findByText("已提交审核")).toBeInTheDocument();
    expect(createAnswerFeedback).toHaveBeenCalledWith({
      course_id: "computer-networks",
      user_id: "student-demo",
      request_id: "req-test",
      question: "TCP 为什么需要三次握手？",
      answer: askResponse.answer,
      reason: "没有解释初始序列号。",
      citation_ids: ["citation-1"],
    });
    await waitFor(() =>
      expect(recordLearningEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          event_type: "feedback_submitted",
          object_id: "feedback-test",
          payload: { request_id: "req-test" },
        }),
      ),
    );
    expect(screen.queryByRole("button", { name: "回答无效" })).not.toBeInTheDocument();
  });

  it("keeps submitted feedback when event recording fails", async () => {
    const user = userEvent.setup();
    const createAnswerFeedback = vi.fn().mockResolvedValue({
      feedback_id: "feedback-event-failed",
      course_id: "computer-networks",
      user_id: "student-demo",
      request_id: "req-test",
      question: "TCP 为什么需要三次握手？",
      answer: askResponse.answer,
      reason: "引用不够准确。",
      citation_ids: ["citation-1"],
      status: "pending_review",
      created_at: "2026-08-18T09:00:00Z",
      reviewer: null,
      reviewed_at: null,
      review_notes: "",
      knowledge_base_change_id: null,
    });
    const recordLearningEvent = vi
      .fn()
      .mockImplementationOnce((event) => Promise.resolve(event))
      .mockRejectedValueOnce(new Error("事件写入失败。"));

    render(
      <ChatPanel
        ask={vi.fn().mockResolvedValue(askResponse)}
        createAnswerFeedback={createAnswerFeedback}
        recordLearningEvent={recordLearningEvent}
      />,
    );

    await user.type(
      screen.getByLabelText("向 AI 助教提问"),
      "TCP 为什么需要三次握手？",
    );
    await user.click(screen.getByRole("button", { name: "发送" }));
    await user.click(await screen.findByRole("button", { name: "回答无效" }));
    await user.type(screen.getByLabelText("请说明回答存在的问题"), "引用不够准确。");
    await user.click(screen.getByRole("button", { name: "提交反馈" }));

    expect(await screen.findByText("已提交审核")).toBeInTheDocument();
    expect(
      await screen.findByText("反馈已提交审核，但学习事件记录失败。"),
    ).toBeInTheDocument();
    expect(createAnswerFeedback).toHaveBeenCalledTimes(1);
  });
});
