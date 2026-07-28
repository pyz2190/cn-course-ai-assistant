import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SystemStatus } from "./SystemStatus";

describe("SystemStatus", () => {
  it("shows the online mock state", async () => {
    render(
      <SystemStatus
        load={async () => ({
          status: "ok",
          service: "cn-course-ai-assistant-api",
          mode: "mock",
        })}
      />,
    );

    expect(await screen.findByText("API 已连接 · Mock 模式")).toBeInTheDocument();
  });

  it("shows a clear offline state", async () => {
    render(<SystemStatus load={async () => Promise.reject(new Error("offline"))} />);

    expect(await screen.findByText("API 未连接")).toBeInTheDocument();
  });
});
