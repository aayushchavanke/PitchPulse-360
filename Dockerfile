FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/matplotlib PREFECT_SERVER_ANALYTICS_ENABLED=false
COPY requirements-platform.txt .
RUN pip install --no-cache-dir --no-compile -r requirements-platform.txt
COPY requirements-extra.txt .
RUN pip install --no-cache-dir --no-compile -r requirements-extra.txt
COPY requirements-container-lock.txt .
RUN pip install --no-cache-dir --no-compile -r requirements-container-lock.txt
COPY . .
CMD ["python", "-m", "platform_lab.cli", "run"]
