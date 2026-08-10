"""
FastAPI Wrapper for Agentic QA Fuzzer.

This module exposes the LangGraph fuzzing logic as an HTTP API. 
It accepts a target URL, runs the fuzzer, and returns the generated
pytest script directly in the response to avoid persistent storage needs.
"""

import os
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import asyncio

try:
    from .agent import run_fuzzer
except ImportError:
    from agent import run_fuzzer

app = FastAPI(
    title="Agentic QA Fuzzer API",
    description="Stateless API to trigger autonomous vulnerability discovery.",
)

# Enable CORS for the GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to your GitHub Pages URL in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FuzzRequest(BaseModel):
    target_url: str


class FuzzResponse(BaseModel):
    success: bool
    message: str
    generated_test_code: str | None = None
    tool_calls_made: int


@app.post("/api/fuzz", response_model=FuzzResponse)
async def fuzz_target(request: FuzzRequest):
    """
    Triggers a fuzzing session against the provided target URL.
    Returns the generated pytest script if a vulnerability is found.
    """
    # Create a temporary directory for this specific fuzzing session
    with tempfile.TemporaryDirectory(prefix="fuzzer_session_") as temp_dir:
        # Pass the temp directory to the MCP server via environment variable
        os.environ["FUZZER_OUTPUT_DIR"] = temp_dir
        
        try:
            # Run the adversarial graph
            final_state = await run_fuzzer(request.target_url)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Fuzzing session failed: {exc}")
            
        messages = final_state.get("messages", [])
        tool_calls_made = sum(len(getattr(m, "tool_calls", []) or []) for m in messages)
        
        # Check if the MCP server wrote any .py files to our temp directory
        temp_path = Path(temp_dir)
        py_files = list(temp_path.glob("test_vulnerability_*.py"))
        
        if not py_files:
            return FuzzResponse(
                success=False,
                message="Session finished but no vulnerability was found (no crash triggered).",
                tool_calls_made=tool_calls_made,
            )
            
        # If we have a file, read it and return its contents directly
        test_file = py_files[0]
        test_code = test_file.read_text(encoding="utf-8")
        
        return FuzzResponse(
            success=True,
            message="Vulnerability found! Generated regression test.",
            generated_test_code=test_code,
            tool_calls_made=tool_calls_made,
        )


@app.get("/health")
def health_check():
    return {"status": "ok"}
