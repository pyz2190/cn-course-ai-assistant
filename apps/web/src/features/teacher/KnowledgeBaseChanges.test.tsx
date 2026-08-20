import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { KnowledgeBaseChangeTask } from "../../api/types";
import { KnowledgeBaseChanges } from "./KnowledgeBaseChanges";

const pendingChange: KnowledgeBaseChangeTask = {
  change_id: "kb-change-001",
  feedback_id: "feedback-001",
  course_id: "computer-networks",
  request_id: "req-001",
  question: "DNS 是如何进行域名解析的？",
  reason: "回答没有说明递归查询与迭代查询的区别。",
  suggested_action: "补充递归查询与迭代查询的对比。",
  status: "pending",
  created_at: "2026-08-20T03:46:12Z",
  handler: null,
  updated_at: null,
  resolution_notes: "",
  resource_ids: [],
};

const listMock = vi.fn();
const updateMock = vi.fn();

vi.mock("../../api/client", () => ({
  listKnowledgeBaseChanges: (...args: unknown[]) => listMock(...args),
  updateKnowledgeBaseChange: (...args: unknown[]) => updateMock(...args),
}));

describe("KnowledgeBaseChanges", () => {
  beforeEach(() => {
    listMock.mockReset().mockResolvedValue([pendingChange]);
    updateMock.mockReset().mockResolvedValue({ ...pendingChange, status: "done" });
  });

  it("shows the real status instead of a hard-coded label", async () => {
    listMock.mockResolvedValue([
      pendingChange,
      {
        ...pendingChange,
        change_id: "kb-change-002",
        status: "done",
        handler: "ta-zhang",
        updated_at: "2026-08-20T04:00:00Z",
        resolution_notes: "已补充对比说明。",
        resource_ids: ["resource-cn-textbook-001"],
      },
    ]);

    render(<KnowledgeBaseChanges />);

    expect(await screen.findByText("待处理")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "全部" }));
    expect(screen.getByText("已完成")).toBeInTheDocument();
    expect(screen.getByText(/由 ta-zhang 处理/)).toBeInTheDocument();
  });

  it("closes a change task as done with handler, notes and resources", async () => {
    const user = userEvent.setup();
    render(<KnowledgeBaseChanges />);

    await user.click(await screen.findByRole("button", { name: "处理" }));
    await user.type(screen.getByLabelText(/处理说明/), "已补充递归与迭代查询的对比切片。");
    await user.type(screen.getByLabelText(/关联资料/), "resource-cn-textbook-001");
    await user.click(screen.getByRole("button", { name: "标记完成" }));

    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith("kb-change-001", {
        status: "done",
        handler: "助教-demo",
        resolution_notes: "已补充递归与迭代查询的对比切片。",
        resource_ids: ["resource-cn-textbook-001"],
      }),
    );
  });

  it("moves a pending task to in_progress", async () => {
    const user = userEvent.setup();
    render(<KnowledgeBaseChanges />);

    await user.click(await screen.findByRole("button", { name: "处理" }));
    await user.click(screen.getByRole("button", { name: "开始处理" }));

    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith(
        "kb-change-001",
        expect.objectContaining({ status: "in_progress" }),
      ),
    );
  });

  it("refuses wont_fix without resolution notes", async () => {
    const user = userEvent.setup();
    render(<KnowledgeBaseChanges />);

    await user.click(await screen.findByRole("button", { name: "处理" }));
    await user.click(screen.getByRole("button", { name: "不予处理" }));

    expect(await screen.findByText("不予处理需要填写处理说明。")).toBeInTheDocument();
    expect(updateMock).not.toHaveBeenCalled();
  });

  it("hides closed tasks from the default open filter", async () => {
    listMock.mockResolvedValue([
      { ...pendingChange, change_id: "kb-change-003", status: "wont_fix", handler: "teacher-li" },
    ]);

    render(<KnowledgeBaseChanges />);

    expect(await screen.findByText("没有未关闭的变更任务。")).toBeInTheDocument();
  });
});
