# API (FastAPI) · build จาก root ของ repo: docker compose build api
# โครงโฟลเดอร์ใน image ต้องเหมือนใน repo เพราะ config.py นับ path จาก root (/app)
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONUTF8=1
WORKDIR /app

COPY services/api/requirements.txt services/api/requirements-model.txt services/api/
RUN pip install --no-cache-dir -r services/api/requirements.txt

# INSTALL_MODEL=1 ติดตั้ง torch (CPU) + transformers สำหรับ MODEL_BACKEND=local · image ใหญ่ขึ้นมาก
ARG INSTALL_MODEL=0
RUN if [ "$INSTALL_MODEL" = "1" ]; then \
      pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
      pip install --no-cache-dir -r services/api/requirements-model.txt; \
    fi

# preprocess.py ใช้ ml/format.py ร่วมกับตอนเทรน
COPY ml/__init__.py ml/format.py ml/
COPY services/api/app services/api/app

WORKDIR /app/services/api
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
