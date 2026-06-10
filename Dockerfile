# r105 Docker image
# Usage:
#   docker build -t r105 .
#   docker run -it --rm r105 --help
#   docker run -it --rm -v ~/.config/r105:/root/.config/r105 r105 chat

FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    bubblewrap \
    nsjail \
    xclip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY r105/ ./r105/

RUN pip install --no-cache-dir .

ENTRYPOINT ["r105"]
CMD ["chat"]
