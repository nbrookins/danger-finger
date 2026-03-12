FROM openscad/openscad:trixie.2025-12-15
WORKDIR /app

# Install Python + minimal runtime deps only (no debug tools in prod image)
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3-pip python3-setuptools python3-venv locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python deps in a single layer
COPY requirements.txt /app/
RUN python3 -m venv /app/.venv \
    && /app/.venv/bin/python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && /app/.venv/bin/pip install --no-binary :all: "ply<4.0,>=3.11" \
    && /app/.venv/bin/python3 -m pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.cache

COPY / /app/

# Verify OpenSCAD from base image
RUN which openscad && echo "OpenSCAD: $(which openscad)" || (echo "OpenSCAD not in PATH" && exit 1)
ENV OPENSCAD_EXEC=openscad
RUN mkdir -p /app/output/preview_temp

ENV script='python3 -u /app/web/server.py $@'
ENV project='danger-finger'
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8081/tcp

COPY --chmod=0755 /docker/entrypoint.sh /app/

ENTRYPOINT ["/app/entrypoint.sh"]
