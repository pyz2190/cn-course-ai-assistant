import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../../App";

/** 教师侧四个模块都要能挂载，避免视图切换或接口改名后仪表盘静默失效。 */
describe("TeacherDashboard", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        const target = String(url);
        const body = target.includes("/health")
          ? { status: "ok", service: "cn-course-ai-assistant-api", mode: "offline" }
          : [];
        return { ok: true, json: async () => body } as Response;
      }),
    );
  });

  it("switches from the student view to the teacher dashboard", async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByLabelText("向 AI 助教提问")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "教师 / 助教视图" }));

    expect(await screen.findByText("教师 / 助教工作台")).toBeInTheDocument();
    for (const tab of ["反馈审核", "知识库变更", "资料上传", "学习行为"]) {
      expect(screen.getByRole("button", { name: tab })).toBeInTheDocument();
    }
  });

  it("shows the pending feedback queue with an empty state", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "教师 / 助教视图" }));

    expect(await screen.findByText("没有待审核的反馈。")).toBeInTheDocument();
  });

  it("returns to the student view", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: "教师 / 助教视图" }));
    await screen.findByText("教师 / 助教工作台");

    await user.click(screen.getByRole("button", { name: "学生视图" }));

    expect(screen.getByLabelText("向 AI 助教提问")).toBeInTheDocument();
    expect(screen.queryByText("教师 / 助教工作台")).not.toBeInTheDocument();
  });
});
