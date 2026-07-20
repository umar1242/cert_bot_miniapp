import { useState } from "react";
import { api } from "../../api";
import type { TakeQuestion } from "../../types";

interface Props {
  attemptId: number;
  question: TakeQuestion;
  onAnswered: (patch: Partial<TakeQuestion>) => void;
  onError: (msg: string) => void;
}

export function Y2Take({ attemptId, question, onAnswered, onError }: Props) {
  const answered = !!question.answered;
  const savedPairs = (question.your_answer?.pairs as Record<string, string>) ?? {};
  const [choice, setChoice] = useState<Record<number, number | "">>(() => {
    const init: Record<number, number | ""> = {};
    (question.lefts ?? []).forEach((l) => { init[l.id] = savedPairs[String(l.id)] ? Number(savedPairs[String(l.id)]) : ""; });
    return init;
  });
  const [correctMap, setCorrectMap] = useState<Record<number, number> | null>(null);
  const [busy, setBusy] = useState(false);

  const allChosen = (question.lefts ?? []).every((l) => choice[l.id] !== "" && choice[l.id] !== undefined);

  async function submit() {
    if (answered || busy || !allChosen) return;
    setBusy(true);
    try {
      const pairs: Record<string, string> = {};
      Object.entries(choice).forEach(([k, v]) => { pairs[k] = String(v); });
      const res = await api.submitAnswer(attemptId, question.id, { pairs });
      setCorrectMap(res.correct_pairs as Record<number, number>);
      onAnswered({
        answered: true,
        your_answer: { pairs },
        is_correct: res.is_correct as boolean,
        points_earned: res.points_earned as number,
      });
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="match-col">
        {(question.lefts ?? []).map((l) => {
          const chosen = choice[l.id];
          let cls = "match-select";
          if (answered && correctMap) cls += chosen === correctMap[l.id] ? " correct" : " wrong";
          return (
            <div className="match-row" key={l.id}>
              <div className="match-left">{l.text}</div>
              <select
                className={cls}
                disabled={answered || busy}
                value={chosen === "" || chosen === undefined ? "" : chosen}
                onChange={(e) => setChoice((c) => ({ ...c, [l.id]: e.target.value ? Number(e.target.value) : "" }))}
              >
                <option value="">— выбрать —</option>
                {(question.rights ?? []).map((r) => (
                  <option key={r.id} value={r.id}>{r.text}</option>
                ))}
              </select>
            </div>
          );
        })}
      </div>

      {!answered && (
        <button className="btn btn-primary" onClick={submit} disabled={!allChosen || busy} style={{ marginTop: 6 }}>
          {busy ? <span className="spinner" /> : "Ответить"}
        </button>
      )}

      {answered && (
        <div className={`feedback-banner ${question.is_correct ? "ok" : "bad"}`}>
          {question.is_correct ? "Все пары верны" : "Есть ошибки"} · {question.points_earned}/{question.points}
        </div>
      )}
    </div>
  );
}
