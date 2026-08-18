import { useState } from "react";
import type { FormEvent } from "react";

import { uploadResource } from "../../api/client";
import type { ResourceUploadResponse } from "../../api/types";

const CONTENT_TYPES = [
  { value: "pdf", label: "PDF 教材/讲义" },
  { value: "ppt", label: "PPT 课件" },
  { value: "subtitle", label: "字幕（SRT/VTT）" },
];

const LANGUAGES = [
  { value: "zh", label: "中文" },
  { value: "en", label: "英文" },
  { value: "bilingual", label: "双语" },
];

export function ResourceUpload() {
  const [courseId, setCourseId] = useState("computer-networks");
  const [title, setTitle] = useState("");
  const [version, setVersion] = useState("v1");
  const [language, setLanguage] = useState("zh");
  const [contentType, setContentType] = useState("pdf");
  const [knowledgePointIds, setKnowledgePointIds] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ResourceUploadResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file || !title.trim()) {
      setError("请选择文件并填写资料标题。");
      return;
    }
    setSubmitting(true);
    setError("");
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("course_id", courseId.trim() || "computer-networks");
      formData.append("title", title.trim());
      formData.append("version", version.trim() || "v1");
      formData.append("language", language);
      formData.append("content_type", contentType);
      formData.append("knowledge_point_ids", knowledgePointIds.trim());
      setResult(await uploadResource(formData));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "资料上传失败。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="teacher-section">
      <div className="teacher-section__head">
        <div>
          <span className="eyebrow">资料导入</span>
          <h3>上传课程资料</h3>
          <p className="teacher-section__desc">
            上传 PDF、PPT 或字幕文件，系统自动解析、切块并向量化入库。
          </p>
        </div>
      </div>

      <form className="upload-form" onSubmit={handleSubmit}>
        <label>
          课程 ID
          <input
            value={courseId}
            onChange={(event) => setCourseId(event.target.value)}
            placeholder="computer-networks"
          />
        </label>
        <label>
          资料标题
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="例如：计算机网络第 4 章课件"
          />
        </label>
        <label>
          版本号
          <input
            value={version}
            onChange={(event) => setVersion(event.target.value)}
            placeholder="v1"
          />
        </label>
        <label>
          文件类型
          <select value={contentType} onChange={(event) => setContentType(event.target.value)}>
            {CONTENT_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          语言
          <select value={language} onChange={(event) => setLanguage(event.target.value)}>
            {LANGUAGES.map((lang) => (
              <option key={lang.value} value={lang.value}>
                {lang.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          关联知识点 ID（逗号分隔，可选）
          <input
            value={knowledgePointIds}
            onChange={(event) => setKnowledgePointIds(event.target.value)}
            placeholder="kp-application-http, kp-network-routing"
          />
        </label>
        <label>
          选择文件
          <input
            type="file"
            accept=".pdf,.pptx,.ppt,.srt,.vtt"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </label>

        {error && <p className="error-message">{error}</p>}

        <button type="submit" className="button-primary" disabled={submitting}>
          {submitting ? "上传解析中…" : "上传并向量化"}
        </button>
      </form>

      {result && (
        <div className={`upload-result upload-result--${result.parse_status}`}>
          <h4>上传结果</h4>
          <p>
            文件：{result.filename} · 资源 ID：{result.resource_id}
          </p>
          <p>
            解析状态：{result.parse_status} · 切块数量：{result.chunk_count}
          </p>
          {result.error && <p className="upload-result__error">错误：{result.error}</p>}
        </div>
      )}
    </div>
  );
}
