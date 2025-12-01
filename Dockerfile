FROM python:3.11-slim

# install node
RUN apt-get update && \
    apt-get install -y nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# prevent Python from writing .pyc & use unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# backend requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy src code for backend and frontend code
COPY src ./src

ENV BACKEND_DIR=/app/src/pokepedai-backend
ENV FRONTEND_DIR=/app/src/pokepedai-frontend

# frontend npm install
RUN cd "$FRONTEND_DIR" && npm install

# 8080 for backend, 3000 for frontend 
EXPOSE 8080 3000

# run flast app
# run npm run dev
CMD bash -lc "\
  cd \"$BACKEND_DIR\" && uvicorn app.main:app --host 0.0.0.0 --port 8080 & \
  cd \"$FRONTEND_DIR\" && npm run dev -- --port 3000 \
"