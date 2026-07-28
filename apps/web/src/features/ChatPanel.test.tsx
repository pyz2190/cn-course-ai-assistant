import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ChatPanel } from "./ChatPanel";

describe("ChatPanel", () => {
  it("renders an answer and its traceable citation", async () => {
    const user = userEvent.setup();
    const ask = vi.fn().mockResolvedValue({
      answer: "三次握手用于同步初始序列号。",
      confidence: 0.92,
      request_id: "req-test",
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
    });

    render(<ChatPanel ask={ask} />);
    await user.click(screen.getByRole("button", { name: "提问" }));

    expect(await screen.findByText("三次握手用于同步初始序列号。")).toBeInTheDocument();
    expect(screen.getByText(/第 3 章 运输层/)).toBeInTheDocument();
    expect(screen.getByText(/第 214–215 页/)).toBeInTheDocument();
  });

  it("shows a readable service error", async () => {
    const user = userEvent.setup();
    render(<ChatPanel ask={vi.fn().mockRejectedValue(new Error("问答服务暂时不可用。"))} />);

    await user.click(screen.getByRole("button", { name: "提问" }));

    expect(await screen.findByText("问答服务暂时不可用。")).toBeInTheDocument();
  });
});
