import type { TaskType } from "../api/types";

export interface TaskTypeMeta {
  label: string;
  /** 卡片主题色，用于类型徽章 */
  tone: string;
  /** 该类型任务的典型学习流程步骤 */
  flow: string[];
  /** 一句话说明该任务类型的学习目标 */
  goal: string;
}

export const TASK_TYPE_META: Record<TaskType, TaskTypeMeta> = {
  foundation: {
    label: "基础学习",
    tone: "green",
    goal: "掌握核心概念与原理，建立知识体系框架。",
    flow: ["阅读资料", "理解概念", "完成自测", "AI 校验", "回顾薄弱点"],
  },
  protocol_analysis: {
    label: "协议分析与仿真",
    tone: "blue",
    goal: "通过抓包与仿真，观察并验证协议交互过程。",
    flow: ["阅读实验指导", "搭建环境", "抓包 / 仿真", "标注关键报文", "提交分析", "AI 检查顺序"],
  },
  case_study: {
    label: "案例分析",
    tone: "amber",
    goal: "运用网络原理分析真实场景，培养知识迁移能力。",
    flow: ["阅读案例背景", "识别关键问题", "知识分析", "提出观点", "AI 检验论据"],
  },
  innovation_challenge: {
    label: "创新挑战",
    tone: "violet",
    goal: "面向开放问题提出创新方案，培养设计思维。",
    flow: ["理解挑战", "研究现有方案", "提出设计思路", "绘制架构图", "AI 追问边界"],
  },
  project_practice: {
    label: "项目实践",
    tone: "rose",
    goal: "综合运用网络知识完成完整工程设计项目。",
    flow: ["分析需求", "设计拓扑", "规划地址", "协议选型", "配置设备", "AI 一致性检查"],
  },
  troubleshooting: {
    label: "排错",
    tone: "slate",
    goal: "基于故障现象与诊断信息，定位根因并修复。",
    flow: ["阅读故障描述", "分析抓包日志", "提出假设", "逐层排查", "AI 评估证据", "确认根因"],
  },
};

export function taskTypeLabel(type: TaskType): string {
  return TASK_TYPE_META[type]?.label ?? type;
}
