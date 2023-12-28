################################################################
FROM python:3.12-alpine as build

# Make sure we use the virtualenv:
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build-pkg

# Install pip requirements
COPY . /build-pkg

RUN apk add --no-cache git  \
    && pip install --no-cache-dir -U pip -r requirements-build.txt  \
    && rm -rf dist  \
    && python -m build  \
    && pip uninstall -r requirements-build.txt -y \
    && pip install --no-cache-dir "$(ls /build-pkg/dist/pygitver-*.tar.gz)"

################################################################
FROM python:3.12-alpine

ENV PYGITVER_TEMPLATE_CHANGELOG="/pygitver/templates/changelog.tmpl"
ENV PYGITVER_TEMPLATE_CHANGELOG_COMMON="/pygitver/templates/changelog-common.tmpl"
ENV PYGITVER_ROOT="/pygitver"

# Install dependencies
RUN apk add --no-cache git openssh

# Copy application code and
COPY ./src/pygitver/templates /pygitver/templates
COPY ./scripts /pygitver/scripts
COPY --from=build /opt/venv /opt/venv

WORKDIR /app

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["pygitver"]
