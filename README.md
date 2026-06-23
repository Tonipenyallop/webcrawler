# webcrawler

# learnt

## Python

- uv(modern, venv under the hood) vs venv
- uv set up(uv init, uv add --dev <dependencyA dependencyB ...>)
- urlsplit, urlunsplit, urljoin
- selectolax vs beautifulsoup
  - pros and cons
- HTMLParser
<!-- **WRONG** - resource creation - (connection/file/pool/handle), shouldn't be in class level
  - **post_init** -> data class
  - **\_init** -> regular class -->
- No hoisting in python
- @classmethod -> when construction requires await - init cannot "await"

```py
# Regular class (and any function/method default)
#  The bug is a mutable object sitting in the default parameter:

  class Cart:
      def __init__(self, items=[]):     # ❌ this [] is created ONCE, shared across all
  Carts
          self.items = items

  # Fix: None sentinel — default to None, then build the real object inside the body:

  class Cart:
      def __init__(self, items=None):       # ✅ default is None (immutable, safe to share)
          self.items = items if items is not None else []   # fresh [] each time, only when needed

  # The pattern is always: immutable sentinel in the signature → create the mutable thing
  # in the body. None is the conventional sentinel. (Why is not None and not items or []?
  # Because or also replaces a legitimately-empty-but-provided list/0/"" — is not None
  # only fills in when the caller truly passed nothing.)


  # Dataclass
  # The bug is a mutable object as a field default:

  @dataclass
  class Cart:
      items: list = []      # ❌ — Python actually refuses this: ValueError, "use default_factory"

  # Fix: field(default_factory=...) — give it a zero-arg callable that produces a fresh
  # value per instance:

  from dataclasses import dataclass, field

  @dataclass
  class Cart:
      items: list = field(default_factory=list)        # ✅ calls list() fresh each instance
      seen: dict = field(default_factory=dict)         # ✅
      client: httpx.AsyncClient = field(
          default_factory=lambda: httpx.AsyncClient(timeout=10))  # ✅ custom object

```

- @dataclass
  - field: default -> value, default_factory -> function(zero arg callable)
- lambda -> anonymous method
- python3 "-m": stands for "module" -> "Look inside your own paths"
  - Rule of thumb: -m → dotted module path, no extension (webcrawler.worker_main); only when you run a file directly do you use the path with .py (python src/webcrawler/worker_main.py). The -m form is what you want here because it sets up the package imports correctly.
- frozenset("RAND_STR".split()) --> 1.split -> 2.frozenset ==> {"RAND_STR"}
  - Because python handles str as "iterable"
  - can be also used like frozenset(["RAND_STR"])

```py
db_dsn = os.environ.get("WEBCRAWLER_DB_URL","")
if db_dsn == '':
        raise Exception(
            "db_dsn failed to fetch. Please set your WEBCRAWLER_DB_URL")


# is same as
db_dsn = os.environ["WEBCRAWLER_DB_URL"]
# automatically throw/raise exception if not set ==> cleaner

```

- selectolax -> HTML parser

## Docker

- service name vs container name
  - exec for service name -> written in docker-compose file
- docker-entrypoint-initdb.d directory for auto run sql command
- "RUN" executes at **build time** (to install things into the image).
- "CMD executes at **start time** (i.g) for -> uv run python3 -m webcrawler.worker_main
- Build docker image

  ```
    docker build -t webcrawler .
  ```

- Check images
  ```
    docker images
  ```
- "docker image prune" for removing <none> tags
- restart "always" -> long running daemon
- restart "no" -> one shot job, such as seeder
- docker-compose up --build -d
  - build for rebuilding docker image
- when updating the service name, make sure updating the host name as well - "HOST_NAME:PORT" breaks

## PSQL

- "Pool" = a connection pool: a managed set of ready-to-use database connections that get reused instead of opening a new one for every query.
- leaking -> pool.fetchval to prevent
- "executemany"
- worker saves all the pages for verifying which page was visited
- worker only parse for html content for next queue
- CONFLICT ON
- RETURNING id
- create_pool -> borrow pool(acquire)
- RESTART IDENTITY -> to restart ID, can be used with TRUNCATE

## Redis

- redis returns by bytes by default, "decode_responses=True" will return with UTF-8 str
- redis-cli LRANGE <KEY_NAME> 0 -1
  - LRANGE stands for list range, "0 -1" means from first to last elem
- redis-cli SMEMBERS <KEY_NAME>
  - SMEMBERS stands for set members

## General

- DSN: (Data Source Name) is a configuration string or data structure that contains the exact information required to connect to a database or data source

# Commands for local testing

- up the html(keep running)

```
uv run python3 http.server 8888
```

- make sure redis is fresh - even if you truncate psql, the same url won't work due to "seen" condition

```
docker-compose exec webcrawler-redis sh && redis-cli FLUSHALL
```

- make sure psql is also clean

```
docker-compose exec webcrawler-db psql -U <USER_NAME> -d <DB_NAME> -c "TRUNCATE tables, links RESTART IDENTITY "
```

- seed first

```
uv run python3 webcrawler.seeder http://localhost:8888/index.html
```

- run worker

```
uv run python3 -m webcrawler.worker_main
```
