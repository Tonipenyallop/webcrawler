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

## Docker

- service name vs container name
  - exec for service name -> written in docker-compose file
- docker-entrypoint-initdb.d directory for auto run sql command

## PSQL

- "Pool" = a connection pool: a managed set of ready-to-use database connections that get reused instead of opening a new one for every query.
- leaking -> pool.fetchval to prevent
- "executemany"
- worker saves all the pages for verifying which page was visited
- worker only parse for html content for next queue
- CONFLICT ON
- RETURNING id
- create_pool -> borrow pool(acquire)
