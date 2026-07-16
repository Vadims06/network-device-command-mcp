FROM python:3.13-alpine3.22

WORKDIR /app
COPY pyproject.toml .
COPY device_command_mcp ./device_command_mcp
RUN pip install --no-cache-dir .

RUN addgroup -g 2001 device-command \
    && adduser -D -H -u 2001 -G device-command device-command \
    && chown -R device-command:device-command /app

USER device-command
EXPOSE 8000
ENTRYPOINT ["fastmcp", "run", "device_command_mcp/server.py:create_server", "--transport", "http", "--host", "0.0.0.0", "--port", "8000", "--no-banner"]
