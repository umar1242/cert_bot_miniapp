import { useState } from "react";
import { api } from "../api";

interface Props {
  variantId: number;
  onImported: (msg: string) => void;
  onError: (msg: string) => void;
}

export function ImportY1({ variantId, onImported, onError }: Props) {
  const [mode, setMode] = useState<"text" | "file">("text");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  async function submitText() {
    if (!text.trim()) return;
    setBusy(true);
    try {
      const res = await api.importY1Text(variantId, text);
      onImported(`Добавлено ${res.added} из ${res.found} заданий`);
      setText("");
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function submitFile(file: File) {
    setBusy(true);
    try {
      const res = await api.importY1File(variantId, file);
      onImported(`Добавлено ${res.added} из ${res.found} заданий`);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card import-panel">
      <span className="label">Импорт текстовой части (Y1)</span>
      <div className="import-tabs">
        <button className={`import-tab ${mode === "text" ? "active" : ""}`} onClick={() => setMode("text")}>
          Вставить текст
        </button>
        <button className={`import-tab ${mode === "file" ? "active" : ""}`} onClick={() => setMode("file")}>
          Загрузить файл
        </button>
      </div>

      {mode === "text" ? (
        <>
          <textarea
            placeholder={"Savol matni?\n=\n#To'g'ri javob\n=\nJavob 2\n=\nJavob 3\n=\nJavob 4\n+\n..."}
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
          />
          <div style={{ marginTop: 10, display: "flex", justifyContent: "flex-end" }}>
            <button className="btn btn-primary" onClick={submitText} disabled={busy || !text.trim()}>
              {busy ? <span className="spinner" /> : "Распознать и добавить"}
            </button>
          </div>
        </>
      ) : (
        <input
          type="file"
          accept=".txt,.docx,.pdf"
          disabled={busy}
          onChange={(e) => e.target.files?.[0] && submitFile(e.target.files[0])}
        />
      )}

      <p className="hint">
        Формат: задания разделяются знаком «+», варианты ответа — знаком «=», правильный вариант
        начинается с «#». Если в задании есть рисунок — отметьте его маркером <code>[рис]</code>{" "}
        рядом с текстом: такое задание попадёт в раздел «нужен рисунок», и рисунок можно будет
        загрузить прямо на листе ответов.
      </p>
    </div>
  );
}
