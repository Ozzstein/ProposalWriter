"""``agency`` command line."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from agency import __version__

app = typer.Typer(help="Proposal Agency — agentic grant-proposal writing.", no_args_is_help=True)


def _ws(root: str | None):
    from agency.workspace import Workspace
    return Workspace.open(root)


@app.callback()
def _main(ctx: typer.Context,
          root: str = typer.Option(None, "--root", envvar="AGENCY_HOME", help="Workspace directory")):
    ctx.obj = {"root": root}


@app.command()
def version():
    typer.echo(__version__)


@app.command()
def init(ctx: typer.Context, name: str, funder: str = typer.Option(None), mechanism: str = typer.Option(None),
         topic: str = typer.Option(None), deadline: str = typer.Option(None),
         hypothesis: str = typer.Option(None), project_id: str = typer.Option(None, "--id")):
    """Create a new proposal project."""
    ws = _ws(ctx.obj["root"])
    p = ws.create_project(name, funder=funder, mechanism=mechanism, topic=topic, deadline=deadline,
                          hypothesis=hypothesis, project_id=project_id)
    typer.echo(json.dumps({"created": p.id, "workspace": str(ws.config.root)}))


@app.command()
def projects(ctx: typer.Context):
    """List projects."""
    ws = _ws(ctx.obj["root"])
    rows = [{"id": p.id, "name": p.name, "funder": p.funder, "current_stage": ws.current_stage(p)}
            for p in ws.list_projects()]
    typer.echo(json.dumps(rows, indent=2))


@app.command()
def status(ctx: typer.Context, project: str):
    """Show project status: stages, gates, graph counts, cost, pending inbox."""
    ws = _ws(ctx.obj["root"])
    typer.echo(json.dumps(ws.status(project), indent=2, default=str))


@app.command()
def gate(ctx: typer.Context, project: str, gate: str, no_write: bool = typer.Option(False, "--no-write")):
    """Evaluate a review gate deterministically. Exit 0 pass, 1 fail, 3 not applicable."""
    ws = _ws(ctx.obj["root"])
    result = ws.check_gate(project, gate, write=not no_write)
    typer.echo(result.model_dump_json(indent=2))
    raise typer.Exit(3 if result.not_applicable else (0 if result.passed else 1))


@app.command("import-legacy")
def import_legacy(ctx: typer.Context, project: str = typer.Argument(None),
                  runs_dir: str = typer.Option(None, "--runs-dir")):
    """Import legacy runs/{project}/ directories into the workspace graph."""
    from agency.legacy.importer import import_legacy_project
    ws = _ws(ctx.obj["root"])
    base = Path(runs_dir) if runs_dir else ws.config.legacy_runs_dir
    dirs = [base / project] if project else [d for d in base.iterdir() if (d / "state.json").exists()]
    for d in dirs:
        counts = import_legacy_project(ws, d)
        typer.echo(json.dumps({"imported": d.name, "counts": counts}))


@app.command("export-graph")
def export_graph(ctx: typer.Context, project: str, out: str = typer.Option(None)):
    """Export a project's nodes and edges as JSONL (git-friendly)."""
    ws = _ws(ctx.obj["root"])
    g = ws.graph(project)
    out_dir = Path(out) if out else ws.config.project_dir(project) / "export"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "nodes.jsonl", "w") as f:
        for n in ws.store.list_nodes(project_id=project):
            f.write(n.model_dump_json() + "\n")
    with open(out_dir / "edges.jsonl", "w") as f:
        for e in g.edges():
            f.write(e.model_dump_json() + "\n")
    typer.echo(json.dumps({"exported": str(out_dir), "nodes": g.summary()}))


@app.command()
def doctor(ctx: typer.Context):
    """Check the installation: SDK, API key, catalogue, packs, database."""
    from agency.doctor import run_doctor
    report = run_doctor(ctx.obj["root"])
    typer.echo(json.dumps(report, indent=2))
    raise typer.Exit(0 if report["ok"] else 1)


@app.command()
def run(ctx: typer.Context, project: str, stage: str,
        flag: list[str] = typer.Option([], "--flag", "-f", help="key=value stage flags"),
        resume: bool = typer.Option(False), force: bool = typer.Option(False)):
    """Run a workflow stage in the terminal (questions are asked on stdin)."""
    from agency.engine.runner import run_stage_cli
    flags = dict(f.split("=", 1) if "=" in f else (f, True) for f in flag)
    code = run_stage_cli(ctx.obj["root"], project, stage, flags=flags, resume=resume, force=force)
    raise typer.Exit(code)


@app.command()
def serve(ctx: typer.Context, host: str = typer.Option(None), port: int = typer.Option(None),
          reload: bool = typer.Option(False)):
    """Start the API server (serves the web UI when built)."""
    import uvicorn

    from agency.server.app import create_app
    ws = _ws(ctx.obj["root"])
    application = create_app(ws)
    uvicorn.run(application, host=host or ws.config.host, port=port or ws.config.port, reload=reload)


@app.command()
def inbox(ctx: typer.Context, project: str = typer.Argument(None), answer: str = typer.Option(None),
          item: str = typer.Option(None)):
    """List pending questions, or answer one: --item ID --answer TEXT."""
    ws = _ws(ctx.obj["root"])
    if item and answer is not None:
        from agency.inbox.service import InboxService
        InboxService(ws).answer(item, {"text": answer})
        typer.echo(json.dumps({"answered": item}))
        return
    rows = [i.model_dump(mode="json") for i in ws.store.list_inbox(project_id=project, status="pending")]
    typer.echo(json.dumps(rows, indent=2, default=str))


@app.command()
def kb(ctx: typer.Context, action: str, arg: str = typer.Argument(None)):
    """Knowledge base: status | promote <project> | query "<question>" | lint | export <dir>."""
    from agency.kb.service import kb_cli
    ws = _ws(ctx.obj["root"])
    typer.echo(json.dumps(kb_cli(ws, action, arg), indent=2, default=str))


if __name__ == "__main__":  # pragma: no cover
    app()
