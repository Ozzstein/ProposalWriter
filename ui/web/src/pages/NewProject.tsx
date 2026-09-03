import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { createProject, uploadInputs } from "@/lib/api";
import { useProjectStore } from "@/stores/project-store";

const PACKS = ["", "innovation-fund", "horizon-europe-ria", "nih-r01", "nsf", "generic"];

const SCOPE_MODULES: Array<[string, string]> = [
  ["finance", "Finance"],
  ["business_plan", "Business plan"],
  ["figures", "Figures"],
  ["external_review", "External review"],
];

export function NewProjectPage(): React.ReactElement {
  const nav = useNavigate();
  const qc = useQueryClient();
  const setActive = useProjectStore((s) => s.setActiveProject);
  const [form, setForm] = useState({ name: "", funder: "", mechanism: "", topic: "", deadline: "", hypothesis: "", pack: "" });
  const [files, setFiles] = useState<File[]>([]);
  const [scope, setScope] = useState<Record<string, string>>({ finance: "", business_plan: "", figures: "", external_review: "" });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: async () => {
      const scope_preferences = Object.fromEntries(
        Object.entries(scope).filter(([, v]) => v === "excluded" || v === "included"),
      ) as Record<string, "excluded" | "included">;
      const p = await createProject({
        name: form.name, funder: form.funder || undefined, mechanism: form.mechanism || undefined,
        topic: form.topic || undefined, deadline: form.deadline || undefined,
        hypothesis: form.hypothesis || undefined, pack: form.pack || undefined,
        scope_preferences: Object.keys(scope_preferences).length ? scope_preferences : undefined,
      });
      if (files.length) await uploadInputs(p.id, files);
      return p;
    },
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      setActive(p.id);
      nav("/");
    },
    onError: (e) => setError(String(e)),
  });

  const field = (key: keyof typeof form, label: string, placeholder = "", textarea = false) => (
    <label className="grid gap-1 text-sm">
      <span className="text-foreground-muted">{label}</span>
      {textarea ? (
        <textarea className="h-28 rounded border border-border bg-background p-2" value={form[key]} placeholder={placeholder} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
      ) : (
        <input className="h-8 rounded border border-border bg-background px-2" value={form[key]} placeholder={placeholder} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
      )}
    </label>
  );

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>New proposal project</CardTitle>
        <CardDescription>
          Step 1 of 3. Upload the call first; you can still explore an idea before the call arrives, and the app aligns it with the
          call afterwards. A firm hypothesis skips the ideation interview. After creating, the Overview tells you what to do next.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3">
        {field("name", "Project name", "Green hydrogen DRI steel")}
        <div className="grid grid-cols-2 gap-3">
          {field("funder", "Funder", "Horizon Europe")}
          {field("mechanism", "Instrument", "RIA")}
        </div>
        <div className="grid grid-cols-2 gap-3">
          {field("topic", "Topic", "one line")}
          {field("deadline", "Deadline", "2026-11-15")}
        </div>
        {field("hypothesis", "Hypothesis / central idea", "Leave empty to develop it in /ideate", true)}
        <label className="grid gap-1 text-sm">
          <span className="text-foreground-muted">Funder pack (auto-detected if empty)</span>
          <select className="h-8 rounded border border-border bg-background px-2" value={form.pack} onChange={(e) => setForm({ ...form, pack: e.target.value })}>
            {PACKS.map((p) => <option key={p} value={p}>{p || "auto"}</option>)}
          </select>
        </label>
        <div className="grid gap-1 text-sm">
          <span className="text-foreground-muted">Optional modules (auto = decide after the call is parsed)</span>
          <div className="grid grid-cols-2 gap-2">
            {SCOPE_MODULES.map(([key, label]) => (
              <label key={key} className="grid gap-1 text-xs">
                <span>{label}</span>
                <select className="h-8 rounded border border-border bg-background px-2" value={scope[key]} onChange={(e) => setScope({ ...scope, [key]: e.target.value })}>
                  <option value="">auto</option>
                  <option value="included">include</option>
                  <option value="excluded">exclude</option>
                </select>
              </label>
            ))}
          </div>
        </div>
        <label className="grid gap-1 text-sm">
          <span className="text-foreground-muted">Call documents / template</span>
          <input type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
        </label>
        {error && <div className="text-xs text-destructive">{error}</div>}
        <div>
          <Button disabled={!form.name.trim() || create.isPending} onClick={() => create.mutate()}>Create project and continue</Button>
        </div>
      </CardContent>
    </Card>
  );
}
