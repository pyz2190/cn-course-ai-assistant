import { afterEach, describe, expect, it, vi } from "vitest";

import { getHealth } from "./client";

describe("API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns a successful payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            status: "ok",
            service: "cn-course-ai-assistant-api",
            mode: "mock",
          }),
          { status: 200 },
        ),
      ),
    );

    await expect(getHealth()).resolves.toMatchObject({ status: "ok" });
  });

  it("maps the stable API error envelope", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            code: "validation_error",
            message: "请求数据不符合接口契约。",
            request_id: "req-test",
            details: null,
          }),
          { status: 422 },
        ),
      ),
    );

    await expect(getHealth()).rejects.toMatchObject(
      expect.objectContaining({
        code: "validation_error",
        requestId: "req-test",
      }),
    );
  });
});
