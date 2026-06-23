# python with builtin uv (https://docs.astral.sh/uv/guides/integration/docker/#installing-uv)
FROM ghcr.io/astral-sh/uv:python3.14-alpine

# Copy the project into the image
COPY . /app

# Disable development dependencies
ENV UV_NO_DEV=1

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

# to find uv 
ENV PATH="/app/.venv/bin:${PATH}"

# how to run - command wanna run 
# worker
CMD ["uv", "run", "python3", "-m", "webcrawler.worker_main"]