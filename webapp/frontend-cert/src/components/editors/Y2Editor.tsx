import type { Y2Pair } from "../../types";

interface Props {
  pairs: Y2Pair[];
  onChange: (pairs: Y2Pair[]) => void;
}

export function Y2Editor({ pairs, onChange }: Props) {
  function update(i: number, field: "left" | "right", value: string) {
    onChange(pairs.map((p, idx) => (idx === i ? { ...p, [field]: value } : p)));
  }
  function remove(i: number) {
    onChange(pairs.filter((_, idx) => idx !== i));
  }
  function add() {
    onChange([...pairs, { left: "", right: "" }]);
  }

  return (
    <div className="field">
      <span className="label">Пары для сопоставления</span>
      {pairs.map((p, i) => (
        <div className="pair-row" key={i}>
          <input type="text" value={p.left} onChange={(e) => update(i, "left", e.target.value)} placeholder="Слева" />
          <input type="text" value={p.right} onChange={(e) => update(i, "right", e.target.value)} placeholder="Справа" />
          <button className="icon-btn" onClick={() => remove(i)} aria-label="Удалить пару">✕</button>
        </div>
      ))}
      <button className="btn btn-ghost" onClick={add}>+ Добавить пару</button>
    </div>
  );
}
