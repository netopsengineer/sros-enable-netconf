#############
# Dependencies
#
#  This base stage just installs the dependencies required for production
#  without any development deps.
ARG PYTHON_VER=3.14
FROM python:${PYTHON_VER} AS base

WORKDIR /usr/src/app

# Install poetry for dep management
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /usr/local/bin/uv
ENV UV_TOOL_BIN_DIR=/usr/local/bin
RUN uv tool install poetry==2.5.1
RUN poetry config virtualenvs.create false

# Install project manifest
COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root --no-interaction

############
# Unit Tests
#
# This test stage runs true unit tests (no outside services) at build time, as
# well as enforcing codestyle and performing fast syntax checks. It is built
# into an image with docker-compose for running the full test suite.
FROM base AS test

COPY . .

RUN poetry install --no-interaction

############
# Linting
#
# Runs all necessary linting and code checks
RUN echo 'Running Flake8' && \
    flake8 . && \
    echo 'Running Black' && \
    black --check --diff . && \
    echo 'Running Pylint' && \
    find . -name '*.py' | xargs pylint  && \
    echo 'Running Yamllint' && \
    yamllint . && \
    echo 'Running pydocstyle' && \
    pydocstyle . && \
    echo 'Running Bandit' && \
    bandit --recursive ./ --configfile .bandit.yml

RUN pytest --color yes -vvv tests

# Run full test suite including integration
ENTRYPOINT ["pytest"]

# Default to running colorful, verbose pytests
CMD ["--cov=sros_enable_netconf", "--color=yes", "-vvv"]
