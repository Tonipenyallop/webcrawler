CREATE TABLE IF NOT EXISTS pages(
    id serial primary key,
    url text not null unique,
    status int,
    content_type text,
    crawled_at  timestamptz default now()
);

CREATE TABLE IF NOT EXISTS links(
    -- id serial primary key ?
    from_page_id int not null references pages(id),
    to_url text not null
);

CREATE INDEX IF NOT EXISTS idx_links_from on links(from_page_id);