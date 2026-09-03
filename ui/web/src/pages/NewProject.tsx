import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { createProject, uploadInputs } from "@/lib/api";
import { useProjectStore } from "@/stores/project-store";

const PACKS = ["", "innovation-fund", "horizon-europe-ria", "nih-r01", "nsf", "generic"];

export function NewProjectPage(): React.ReactElement {
  const nav = useNavigate();
  const qc = useQueryClient();
  const setActive = useProjectStore((s) => s.setActiveProject);
  const [form, setForm] = useState({ name: "", funder: "", mechanism: "", topic: "", deadline: "", hypothesis: "", pack: "" });
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: async () => {
      const p = await createProject({
        name: form.name, funder: form.funder || undefined, mechanism: form.mechanism || undefined,
        topic: form.topic || undefined, deadline: form.deadline || undefined,
        hypothesis: form.hypothesis || undefined, pack: form.pack || undefined,
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
          Step 1 of 3. A firm hypothesis skips ideation; leave it empty to develop the idea in an interview. Upload the call document
          (and the official template if you have it) now or on the next screen. After creating, the Overview tells you what to do next.
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
