# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install into a virtual environment so stage 2 can take it in a single COPY
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Dependencies change rarely, code changes constantly.
# Installing before copying the code means a code edit reuses this cached layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---------- Stage 2: runtime ----------
FROM python:3.12-slim

# Only the finished venv crosses over. pip, its cache and any build tools stay behind.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Logs appear immediately instead of sitting in a buffer
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# A normal user with no privileges
RUN useradd --create-home --uid 1000 appuser

# root copies the code, so root owns it: appuser can run it but cannot rewrite it
COPY app/ ./app/

# Drop privileges last, after everything that needed root
USER appuser

EXPOSE 8000

# slim images have no curl, so the check uses Python itself
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]