"""Deploy / redeploy del Agente Supervisor Académico en EasyPanel.

Servicio NUEVO `agente-academico` en el proyecto `maple-v3` (mismo panel y misma
Supabase `veic` que Sofía Pro). Source = GitHub `rrintecai-sudo/agente-academico`
con build Dockerfile. autoDeploy=False → cada `git push` se publica corriendo
este script con --redeploy.

La env se DERIVA de la del servicio `sofia-pro` (mismas claves Anthropic/Supabase),
filtrando solo lo que el agente necesita y forzando modelo Sonnet + puerto 8010.

Uso:
    export EASYPANEL_URL=...            # http://72.62.160.162:3000
    export EASYPANEL_API_TOKEN=...      # token de la API de EasyPanel
    uv run python scripts/deploy_easypanel.py            # full (crea + configura + deploy)
    uv run python scripts/deploy_easypanel.py --redeploy  # solo redeploy (tras git push)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PROJECT = os.getenv("EASYPANEL_PROJECT", "maple-v3")
SERVICE = os.getenv("EASYPANEL_SERVICE", "agente-academico")
SRC_SERVICE = os.getenv("EASYPANEL_SERVICE_SRC", "sofia-pro")  # de quien copiamos env base
GH_OWNER = "rrintecai-sudo"
GH_REPO = "agente-academico"
GH_REF = "main"
DOMAIN = "agente-academico.cxjnjn.easypanel.host"
INTERNAL_PORT = 8010
MODEL = "claude-sonnet-4-6"

# Claves que el agente necesita (el resto de la env de Sofía se descarta).
KEEP = {
    "ANTHROPIC_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_DB_URL",
    "ADMIN_API_KEY",
}


def _hdr() -> dict[str, str]:
    return {"Authorization": f"Bearer {os.environ['EASYPANEL_API_TOKEN']}", "Content-Type": "application/json"}


def _base() -> str:
    return os.environ["EASYPANEL_URL"].rstrip("/")


def _post(proc: str, payload: dict) -> tuple[int, object]:
    req = urllib.request.Request(
        f"{_base()}/api/trpc/{proc}", data=json.dumps({"json": payload}).encode(), headers=_hdr(), method="POST"
    )
    try:
        r = urllib.request.urlopen(req, timeout=120)
        return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400].decode(errors="replace")


def _get(proc: str, payload: dict) -> object:
    url = f"{_base()}/api/trpc/{proc}?input=" + urllib.parse.quote(json.dumps({"json": payload}))
    req = urllib.request.Request(url, headers=_hdr())
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read()[:300].decode(errors="replace")}


def _env_agente() -> str:
    """Deriva la env del servicio sofia-pro: filtra a KEEP y añade overrides."""
    d = _get("services.app.inspectService", {"projectName": PROJECT, "serviceName": SRC_SERVICE})
    env = d.get("json", {}).get("env", "") if isinstance(d, dict) else ""
    out = []
    for line in env.splitlines():
        key = line.split("=", 1)[0].strip()
        if key in KEEP:
            out.append(line)
    out.append(f"ANTHROPIC_MODEL_PRINCIPAL={MODEL}")
    out.append(f"APP_PORT={INTERNAL_PORT}")
    out.append("ENV=production")
    return "\n".join(out)


def main() -> int:
    if "EASYPANEL_URL" not in os.environ or "EASYPANEL_API_TOKEN" not in os.environ:
        print("ERROR: exporta EASYPANEL_URL y EASYPANEL_API_TOKEN.", file=sys.stderr)
        return 2

    redeploy_only = "--redeploy" in sys.argv
    if not redeploy_only:
        print("createService:", _post("services.app.createService", {"projectName": PROJECT, "serviceName": SERVICE}))
        print("updateSourceGithub:", _post("services.app.updateSourceGithub", {
            "projectName": PROJECT, "serviceName": SERVICE,
            "owner": GH_OWNER, "repo": GH_REPO, "ref": GH_REF, "path": "/", "autoDeploy": False,
        }))
        print("updateBuild:", _post("services.app.updateBuild", {
            "projectName": PROJECT, "serviceName": SERVICE, "build": {"type": "dockerfile", "file": "./Dockerfile"},
        }))
        print("updateEnv:", _post("services.app.updateEnv", {
            "projectName": PROJECT, "serviceName": SERVICE, "env": _env_agente(),
        }))
        print("updateDeploy:", _post("services.app.updateDeploy", {
            "projectName": PROJECT, "serviceName": SERVICE, "replicas": 1, "command": None, "zeroDowntime": True,
        }))
        # Dominio público apuntando al puerto interno del agente.
        print("createDomain:", _post("domains.createDomain", {
            "projectName": PROJECT, "serviceName": SERVICE,
            "domain": {"host": DOMAIN, "https": True, "port": INTERNAL_PORT, "path": "/"},
        }))

    print("deployService:", _post("services.app.deployService", {
        "projectName": PROJECT, "serviceName": SERVICE, "forceRebuild": True,
    }))
    print(f"\nListo. Health: https://{DOMAIN}/readyz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
