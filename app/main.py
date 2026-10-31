"""FastAPI application: secure upload -> Gemma 4 analysis (streamed live) -> verified result."""
from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Iterator

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import Settings, load_settings
from .extract import UploadError, extract_text, safe_name
from .llm import LLM, NO_KEY_MESSAGE, ConfigError, LLMError
from .prompts import build_prompt
from .security import SECURITY_HEADERS, RateLimiter, client_ip
from .verify import ParseError, parse_analysis, verify_quotes

log = logging.getLogger("proof2motion")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def create_app(settings: Settings | None = None, llm: LLM | None = None) -> FastAPI:
    settings = settings or load_settings()
    llm = llm or LLM(settings)
    limiter = RateLimiter(settings.rate_limit_per_minute)

    app = FastAPI(
        title="Proof2Motion",
        version=__version__,
        docs_url=None if settings.production else "/api/docs",
        openapi_url=None if settings.production else "/api/openapi.json",
        redoc_url=None,
    )

    origins = list(settings.allowed_origins)
    if not settings.production:
        origins += ["http://localhost:5173", "http://127.0.0.1:5173"]
    if origins:
        app.add_middleware(
            CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"]
        )

    @app.middleware("http")
    async def guard(request: Request, call_next):
        length = request.headers.get("content-length", "")
        if length.isdigit() and int(length) > settings.max_request_bytes:
            return JSONResponse({"detail": "Upload too large."}, status_code=413)
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if settings.production and proto == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        path = request.url.path
        if path.startswith("/assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception):
        ref = uuid.uuid4().hex[:8]
        log.exception("unhandled error ref=%s", ref)
        return JSONResponse({"detail": f"Something went wrong. Reference: {ref}"}, status_code=500)

    def throttle(request: Request) -> None:
        limiter.check(client_ip(request, settings.trust_proxy))

    # ---------- helpers ----------

    async def prepare(files: list[UploadFile]) -> tuple[str, dict[str, str], list[str]]:
        if not files:
            raise HTTPException(400, "Upload at least one file.")
        if len(files) > settings.max_files:
            raise HTTPException(400, f"Upload at most {settings.max_files} files at a time.")
        corpus: dict[str, str] = {}
        try:
            for upload in files:
                name = safe_name(upload.filename)
                data = await upload.read(settings.max_file_bytes + 1)
                if len(data) > settings.max_file_bytes:
                    raise UploadError(f"'{name}' is larger than {settings.max_file_bytes // 1_048_576} MB.", 413)
                if not data:
                    continue
                text = (await run_in_threadpool(extract_text, name, data, settings)).strip()
                if not text:
                    raise UploadError(f"'{name}' has no readable text (a scanned PDF?). Upload a text-based file.")
                while name in corpus:
                    name = f"copy-{name}"
                corpus[name] = text[: settings.max_chars_per_file]
        except UploadError as exc:
            raise HTTPException(exc.status, str(exc)) from exc
        if not corpus:
            raise HTTPException(400, "No readable evidence found.")
        prompt, used = build_prompt(corpus, settings.max_chars_total)
        return prompt, used, list(used)

    def run(prompt: str, corpus: dict[str, str], names: list[str]) -> Iterator[tuple[str, dict]]:
        """Sync generator of (event, data). Runs in a worker thread when streamed."""
        yield "stage", {"stage": "analyzing"}
        text, model = "", ""
        try:
            for item in llm.stream(prompt):
                if item[0] == "progress":
                    yield "progress", {"chars": item[1]}
                else:
                    text, model = item[1], item[2]
            try:
                analysis = parse_analysis(text)
            except ParseError as exc:
                log.warning("unparseable output, retrying once: %s", exc)
                yield "stage", {"stage": "retrying"}
                text, model = llm.generate(prompt)
                analysis = parse_analysis(text)
        except ConfigError as exc:
            yield "error", {"detail": str(exc), "status": 500}
            return
        except (LLMError, ParseError) as exc:
            ref = uuid.uuid4().hex[:8]
            log.error("analysis failed ref=%s: %s", ref, exc)
            yield "error", {"detail": f"The AI could not produce a valid analysis. Please try again. (ref {ref})", "status": 502}
            return
        yield "stage", {"stage": "verifying"}
        stats = verify_quotes(analysis, corpus)
        yield "result", {
            "status": "success",
            "model": model,
            "files": names,
            "analysis": analysis.model_dump(),
            "verification": stats,
        }

    # ---------- API ----------

    @app.get("/api/health")
    def health():
        return {"ok": True, "ai_ready": llm.ready, "model": settings.model, "version": __version__}

    @app.get("/api/sample")
    def sample():
        if not settings.sample_file.is_file():
            raise HTTPException(404, "Sample file not found.")
        return {"filename": settings.sample_file.name, "text": settings.sample_file.read_text(encoding="utf-8")}

    @app.post("/api/analyze", dependencies=[Depends(throttle)])
    async def analyze(files: list[UploadFile] = File(...)):
        prompt, corpus, names = await prepare(files)

        def consume():
            for event, data in run(prompt, corpus, names):
                if event == "result":
                    return data
                if event == "error":
                    raise HTTPException(data.get("status", 502), data["detail"])

        return await run_in_threadpool(consume)

    @app.post("/api/analyze/stream", dependencies=[Depends(throttle)])
    async def analyze_stream(files: list[UploadFile] = File(...)):
        prompt, corpus, names = await prepare(files)
        if not llm.ready:
            raise HTTPException(500, NO_KEY_MESSAGE)

        def body():
            try:
                for event, data in run(prompt, corpus, names):
                    yield _sse(event, data)
            except Exception:  # noqa: BLE001
                ref = uuid.uuid4().hex[:8]
                log.exception("stream failed ref=%s", ref)
                yield _sse("error", {"detail": f"Something went wrong. Reference: {ref}", "status": 500})

        return StreamingResponse(
            body(), media_type="text/event-stream", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"}
        )

    # ---------- built frontend (single-process deploy) ----------

    dist = settings.dist_dir
    if dist.is_dir() and (dist / "index.html").is_file():
        root = dist.resolve()
        if (root / "assets").is_dir():
            app.mount("/assets", StaticFiles(directory=root / "assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            if full_path.startswith("api/"):
                raise HTTPException(404, "Not found.")
            candidate = (root / full_path).resolve()
            if full_path and candidate.is_file() and root in candidate.parents:
                return FileResponse(candidate)
            return FileResponse(root / "index.html", headers={"Cache-Control": "no-cache"})
    else:

        @app.get("/", include_in_schema=False)
        def home():
            return {"message": "Proof2Motion API is running. Build the frontend (npm run build) to serve the UI here."}

    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = create_app()
