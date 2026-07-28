import { useEffect, useState } from "react";

import { getHealth } from "../api/client";
import type { HealthResponse } from "../api/types";

type Props = {
  load?: () => Promise<HealthResponse>;
};

export function SystemStatus({ load = getHealth }: Props) {
  const [status, setStatus] = useState<"loading" | "online" | "offline">("loading");

  useEffect(() => {
    let active = true;
    load()
      .then(() => {
        if (active) setStatus("online");
      })
      .catch(() => {
        if (active) setStatus("offline");
      });
    return () => {
      active = false;
    };
  }, [load]);

  const labels = {
    loading: "正在连接 API",
    online: "API 已连接 · Mock 模式",
    offline: "API 未连接",
  };

  return (
    <div className={`status status--${status}`} role="status">
      <span className="status__dot" aria-hidden="true" />
      {labels[status]}
    </div>
  );
}
