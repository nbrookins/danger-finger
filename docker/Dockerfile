FROM openscad/openscad:trixie.2025-12-15
WORKDIR /app

#install python and extras
RUN apt-get update && apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        curl iputils-ping locales nano wget \
        python3-pip python3-setuptools python3-venv \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
    #apt-transport-https gcc build-essential locales

#install python deps
COPY requirements.txt /app/
#RUN python3 -m venv .venv && DEBIAN_FRONTEND=noninteractive .venv/bin/python3 -m pip install --no-cache-dir --upgrade pip \
#    && .venv/bin/python3 -m pip install --no-cache-dir -r requirements.txt \
 #  && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN python3 -m venv /app/.venv && DEBIAN_FRONTEND=noninteractive /app/.venv/bin/python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel
RUN /app/.venv/bin/pip install --no-binary :all: "ply<4.0,>=3.11"
RUN /app/.venv/bin/python3 -m pip install --no-cache-dir -r requirements.txt && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY / /app/

# Ensure OpenSCAD is available (base image is openscad/openscad)
RUN which openscad && echo "OpenSCAD: $(which openscad)" || (echo "OpenSCAD not in PATH" && exit 1)
ENV OPENSCAD_EXEC=openscad
# Working dir for preview temp files
RUN mkdir -p /app/output/preview_temp

#fill vars, copy our source and make executable
ENV script='python3 -u /app/web/server.py $@'
ENV project='danger-finger'
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8081/tcp

COPY --chmod=0755 /docker/entrypoint.sh /app/

ENTRYPOINT ["/app/entrypoint.sh"]
#ENTRYPOINT ["/bin/bash"]
