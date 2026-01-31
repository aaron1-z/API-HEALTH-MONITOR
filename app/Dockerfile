FROM python:3.9-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# In a real production environment, we might use a distroless image or alpine, but slim is fine for this assignment.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
