# webcrawler

# learnt

## Python

- uv(modern, venv under the hood) vs venv
- uv set up(uv init, uv add --dev <dependencyA dependencyB ...>)
- urlsplit, urlunsplit, urljoin
- selectolax vs beautifulsoup
  - pros and cons
- HTMLParser
- resource creation - (connection/file/pool/handle), shouldn't be in class level
  - **post_init** -> data class
  - **\_init** -> regular class
- No hoisting in python

## Docker

- service name vs container name
  - exec for service name -> written in docker-compose file
- docker-entrypoint-initdb.d directory for auto run sql command

## PSQL

- "Pool" = a connection pool: a managed set of ready-to-use database connections that get reused instead of opening a new one for every query.
- leaking -> pool.fetchval to prevent
- "executemany"
