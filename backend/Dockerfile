FROM python:3.10-slim

WORKDIR /app

# tesseract-ocr: native OCR engine used via pytesseract -- far lighter than
# a torch-based OCR model, which matters on a memory-constrained instance.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
