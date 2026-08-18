import { render, screen } from "@testing-library/react";
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
});
