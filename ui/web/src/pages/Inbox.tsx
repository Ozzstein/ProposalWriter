import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { answerInbox, listInbox } from "@/lib/api";
import { useProjectStore } from "@/stores/project-store";
import type { InboxItem } from "@pw/shared";

export function InboxPage(): React.ReactElement {
  const active = useProjectStore((s) => s.activeProject);
  const qc = useQueryClient();
  const [showAll, setShowAll] = useState(false);
  const { data, isLoading, error } = useQuery({
    queryKey: ["inbox", active, showAll],
    queryFn: () => listInbox(active ?? undefined, showAll ? "all" : "pending"),
    refetchInterval: 2000,
  });
  const answer = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) => answerInbox(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["inbox"] });
      qc.invalidateQueries({ queryKey: ["runs"] });
    },
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 text-xs text-foreground-muted">
        <span>{data?.length ?? 0} item(s)</span>
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} /> show answered
        </label>
        {answer.error && <span className="text-destructive">{String(answer.error)}</span>}
      </div>
      {isLoading ? (
        <div className="text-sm text-foreground-muted">Loading…</div>
      ) : error ? (
        <div className="text-sm text-destructive">{String(error)}</div>
      ) : (data ?? []).length === 0 ? (
        <Card><CardHeader><CardTitle>Inbox empty</CardTitle><CardDescription>Runs that need you will post here and pause until you answer.</CardDescription></CardHeader></Card>
      ) : (
        (data ?? []).map((item) => (
          <InboxCard key={item.id} item={item} disabled={answer.isPending} onAnswer={(body) => answer.mutate({ id: item.id, body })} />
        ))
      )}
    </div>
  );
}

function InboxCard({ item, onAnswer, disabled }: { item: InboxItem; onAnswer: (body: Record<string, unknown>) => void; disabled: boolean }): React.ReactElement {
  const answered = item.status !== "pending";
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Badge variant={answered ? "muted" : "info"}>{item.kind}</Badge>
          <CardTitle className="text-base">{item.header}</CardTitle>
          <span className="ml-auto mono text-[11px] text-foreground-muted">{item.run_id ?? ""}</span>
        </div>
        <CardDescription className="whitespace-pre-wrap">{item.question}</CardDescription>
      </CardHeader>
      <CardContent>
        {answered ? (
          <pre className="mono max-h-40 overflow-auto text-[11px] text-foreground-muted">{JSON.stringify(item.answer, null, 2)}</pre>
        ) : item.kind === "question" ? (
          <QuestionForm item={item} onAnswer={onAnswer} disabled={disabled} />
        ) : item.kind === "approval" ? (
          <ApprovalForm item={item} onAnswer={onAnswer} disabled={disabled} />
        ) : item.kind === "form" ? (
          <JsonForm item={item} onAnswer={onAnswer} disabled={disabled} />
        ) : (
          <ChatForm item={item} onAnswer={onAnswer} disabled={disabled} />
        )}
      </CardContent>
    </Card>
  );
}

type FormProps = { item: InboxItem; onAnswer: (body: Record<string, unknown>) => void; disabled: boolean };

function QuestionForm({ item, onAnswer, disabled }: FormProps): React.ReactElement {
  const options = (item.payload.options ?? []).map((o) => (typeof o === "string" ? { label: o } : o));
  const multi = !!item.payload.multi;
  const [chosen, setChosen] = useState<string[]>([]);
  const [text, setText] = useState("");
  const submit = () => {
    const choice = multi ? chosen : chosen[0] ?? text;
    onAnswer({ choice: choice || text, choices: chosen, text });
  };
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {options.map((o) => {
          const on = chosen.includes(o.label);
          return (
            <Button key={o.label} size="sm" variant={on ? "primary" : "secondary"} title={o.description}
              onClick={() => setChosen(multi ? (on ? chosen.filter((c) => c !== o.label) : [...chosen, o.label]) : [o.label])}>
              {o.label}
            </Button>
          );
        })}
      </div>
      <div className="flex gap-2">
        <input className="h-8 flex-1 rounded border border-border bg-background px-2 text-sm" placeholder="or type an answer / a note"
          value={text} onChange={(e) => setText(e.target.value)} />
        <Button size="sm" disabled={disabled || (!chosen.length && !text.trim())} onClick={submit}>Send</Button>
      </div>
    </div>
  );
}

function ApprovalForm({ item, onAnswer, disabled }: FormProps): React.ReactElement {
  const rows = item.payload.rows ?? [];
  const decisions = item.payload.decisions ?? ["approve", "reject", "defer"];
  const [choice, setChoice] = useState<Record<string, string>>(Object.fromEntries(rows.map((r) => [r.id, decisions[0]!])));
  const [note, setNote] = useState("");
  const setAll = (d: string) => setChoice(Object.fromEntries(rows.map((r) => [r.id, d])));
  const overall = Object.values(choice).every((d) => d === decisions[0]) ? decisions[0] : "custom";
  return (
    <div className="space-y-2">
      <div className="flex gap-2 text-xs">
        {decisions.map((d) => (
          <Button key={d} size="sm" variant="secondary" onClick={() => setAll(d)}>{d} all</Button>
        ))}
      </div>
      <div className="max-h-96 overflow-auto rounded border border-border">
        <table className="w-full text-xs">
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-border">
                <td className="mono px-2 py-1 text-foreground-muted">{r.id}</td>
                <td className="px-2 py-1">{r.summary}</td>
                <td className="px-2 py-1">
                  <select className="h-7 rounded border border-border bg-background px-1" value={choice[r.id]} onChange={(e) => setChoice({ ...choice, [r.id]: e.target.value })}>
                    {decisions.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex gap-2">
        <input className="h-8 flex-1 rounded border border-border bg-background px-2 text-sm" placeholder="note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
        <Button size="sm" disabled={disabled} onClick={() => onAnswer({ decision: overall, rows: choice, note })}>Submit</Button>
      </div>
    </div>
  );
}

type Prop = { type?: string; enum?: string[]; title?: string; description?: string; readOnly?: boolean };

function JsonForm({ item, onAnswer, disabled }: FormProps): React.ReactElement {
  const schema = item.payload.schema as { properties?: Record<string, Prop> } | undefined;
  const props = schema?.properties;
  const keys = props ? Object.keys(props) : [];
  const simpleText = keys.length === 1 && props![keys[0]!]?.type === "string" && !props![keys[0]!]?.enum;
  const fieldForm = keys.length > 1 && keys.every((k) => props![k]?.type === "string");
  const example = (item.payload.example ?? {}) as Record<string, string>;
  const [text, setText] = useState(Object.keys(example).length && !fieldForm ? JSON.stringify(example, null, 2) : "");
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(keys.map((k) => [k, example[k] ?? props![k]?.enum?.[0] ?? ""])));
  const [err, setErr] = useState<string | null>(null);
  if (fieldForm) {
    return (
      <div className="space-y-2">
        {keys.map((k) => {
          const p = props![k]!;
          return (
            <label key={k} className="grid gap-1 text-sm">
              <span>{p.title ?? k}{p.description ? <span className="text-xs text-foreground-muted"> — {p.description}</span> : null}</span>
              {p.enum ? (
                <select className="h-8 rounded border border-border bg-background px-2" value={values[k]} disabled={p.readOnly || disabled}
                  onChange={(e) => setValues({ ...values, [k]: e.target.value })}>
                  {p.enum.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              ) : (
                <input className="h-8 rounded border border-border bg-background px-2" value={values[k]} disabled={p.readOnly || disabled}
                  onChange={(e) => setValues({ ...values, [k]: e.target.value })} />
              )}
            </label>
          );
        })}
        <Button size="sm" disabled={disabled} onClick={() => onAnswer({ data: values })}>Submit</Button>
      </div>
    );
  }
  const submit = () => {
    if (simpleText) {
      onAnswer({ data: { [keys[0]!]: text }, text });
      return;
    }
    try {
      onAnswer({ data: JSON.parse(text) });
      setErr(null);
    } catch (e) {
      setErr(`Invalid JSON: ${String(e)}`);
    }
  };
  return (
    <div className="space-y-2">
      <textarea className="mono h-48 w-full rounded border border-border bg-background p-2 text-xs" value={text} onChange={(e) => setText(e.target.value)}
        placeholder={simpleText ? "Paste text here" : "JSON matching payload.schema"} />
      {!simpleText && schema && (
        <details className="text-xs text-foreground-muted"><summary>schema</summary><pre className="mono max-h-40 overflow-auto">{JSON.stringify(schema, null, 2)}</pre></details>
      )}
      {err && <div className="text-xs text-destructive">{err}</div>}
      <Button size="sm" disabled={disabled || !text.trim()} onClick={submit}>Submit</Button>
    </div>
  );
}

function ChatForm({ item, onAnswer, disabled }: FormProps): React.ReactElement {
  const [text, setText] = useState("");
  return (
    <div className="space-y-2">
      {item.payload.transcript && <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded border border-border p-2 text-xs">{item.payload.transcript}</pre>}
      <div className="flex gap-2">
        <textarea className="h-20 flex-1 rounded border border-border bg-background p-2 text-sm" value={text} onChange={(e) => setText(e.target.value)} placeholder="Your reply" />
        <Button size="sm" disabled={disabled || !text.trim()} onClick={() => onAnswer({ text })}>Send</Button>
      </div>
    </div>
  );
}
