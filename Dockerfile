FROM python:3.12-alpine as build

ENV SEMVER_HELPER_TEMPLATE_CHANGELOG="/pygitver/templates/changelog.tmpl"
ENV SEMVER_HELPER_ROOT="/pygitver"

# Make sure we use the virtualenv:
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install pip requirements
COPY ./requirements.txt /pygitver/requirements.txt
RUN pip install --no-cache-dir -U pip  \
    && pip install --no-cache-dir -r /pygitver/requirements.txt

FROM python:3.12-alpine

# Install dependencies
RUN apk add --no-cache git openssh \
    && ln -s /pygitver/pygitver /usr/local/bin/pygitver

# Copy application code and
COPY ./src /pygitver
COPY ./scripts /pygitver/scripts
COPY --from=build /opt/venv /opt/venv

WORKDIR /app

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["python", "/pygitver/pygitver.py"]
