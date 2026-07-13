# Optional container image. The tool is normally installed with pipx/pip;
# this is for running it in a container without a local Python.
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

# Run as non-root.
RUN useradd -u 10001 app
USER app

ENTRYPOINT ["carbon-region-picker"]
