FROM ubuntu:18.04
#most of this came from python:3, but was more elegant to override rather than inherit, dur to sql install

# apt-get system utilities
RUN apt-get update && apt-get upgrade -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        curl iputils-ping apt-transport-https \
        gcc build-essential g++-5 \
        locales nano wget \
        python3-pip python3-setuptools python-pip \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#get project name from arg
ARG project
ENV project $project
ARG script
ENV script $script
ARG py3
ENV py3 $py3

ENV script 'python3 -u utility.py $$@'
ENV project 'danger-finger'

#install python deps
COPY requirements.txt /
RUN DEBIAN_FRONTEND=noninteractive python$py3 -m pip install --no-cache-dir --upgrade pip \
    && python$py3 -m pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#install openscad
RUN wget -qO - https://files.openscad.org/OBS-Repository-Key.pub | apt-key add - \
    && echo "deb https://download.opensuse.org/repositories/home:/t-paul/xUbuntu_18.04/ ./" > /etc/apt/sources.list.d/openscad.list \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        openscad-nightly \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#the below should generally be replicated in child dockerfiles
#copy our source and make executable
COPY . /
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
