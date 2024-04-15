FROM python:3.11.7-slim-bullseye

LABEL "com.github.actions.name"="Devfile Registry Stack Maintainer"
LABEL "com.github.actions.description"="Takes care of the registry stack lifecycle"
LABEL "repository"="http://github.com/thepetk/devfile_registry_maintainer"
LABEL "homepage"="http://github.com/actions"
LABEL "maintainer"="thepetk <thepetk@gmail.com>"

WORKDIR /github/workspace/

COPY entrypoint.sh /entrypoint.sh
COPY requirements.txt /requirements.txt
COPY maintainer.py /maintainer.py

RUN pip install -r /requirements.txt

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]