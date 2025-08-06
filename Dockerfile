# syntax=docker/dockerfile:1
FROM python:3.10-alpine as builder
WORKDIR /build

RUN apk add --no-cache gcc musl-dev linux-headers

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

FROM python:3.10-alpine
WORKDIR /bot

COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache /wheels/*

COPY main.py .
RUN addgroup --gid 1001 --system bot && \
    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system bot

RUN mkdir /bot/state
RUN chown -R bot:bot /bot/state
USER bot:bot
STOPSIGNAL SIGINT
CMD ["python3", "main.py"]
