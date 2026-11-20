FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
WORKDIR /data
EXPOSE 8501
CMD ["streamlit", "run", "/app/src/movebank/presentation/streamlit/app.py", "--server.address=0.0.0.0", "--server.headless=true"]
