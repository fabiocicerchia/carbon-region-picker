# Optional container image. The tool is normally installed with pipx/pip;
# this is for running it in a container without a local Python.
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

# Run as non-root.
RUN useradd -u 10001 app
USER app

# One-shot CLI tool, not a service — this just confirms the interpreter starts.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=1 \
    CMD ["python3", "-c", "import sys; sys.exit(0)"]

ENTRYPOINT ["carbon-region-picker"]
