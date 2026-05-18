# ongo-site — publishing, generating, serving

`ongo-site` turns the **kendb publish set** into a self-contained static
website. Nothing is published unless you explicitly mark it with an
`ongo-web` publication, so the published surface is always explicit and
queryable.

## 1. Mark content for publish

The `ongo-web` publication kind is the publish marker:

| field   | meaning                                             |
|---------|-----------------------------------------------------|
| `key`   | the target publication's id (or its key)            |
| `title` | the display title / nav label on the site           |
| notes   | optional section/topic override (kendb notes body)  |

Mark an existing note for publish (the exact command):

```bash
ken add ongo-web -k <note-id> --title "<nav title>"
```

For example, to publish the note with id `66f290ec-...`:

```bash
ken add ongo-web -k 66f290ec-4aa6-463f-8779-6a06a9c428ac \
  --title "AI in Poetry and Literary Arts"
```

`-k` accepts either the publication **id** or its **key** (slug, path, URL).
To unpublish, delete the `ongo-web` marker (not the source note):

```bash
ongo-delete pub --key <note-id>      # removes only the ongo-web marker
```

Items are grouped on the index page by the topics they are related to in the
kendb relationship graph (`related-to` / `cites` / `derives-from` to a
`topic` publication). Items with no topic relationship land under
"Other notes". Putting text in the `ongo-web` marker's kendb notes body
overrides the section heading for that item.

## 2. Generate the site

```bash
bin/ongo-site                        # writes ./site/ (deterministic)
bin/ongo-site --out /opt/ongo/site   # custom output directory
bin/ongo-site --ken /path/to/ken --db /path/to/ken.db
```

The generator is stdlib-only, idempotent, and rewrites the output directory
cleanly — it is safe to run every self-improvement cycle. Source bodies are
resolved from (in order) a filesystem `.md`/`.pdf`/`.tex` named by the
publication key, a slug match under the note roots, the kendb note body via
`ken show --json` (zomglings/ken#8, **ken ≥ v3** — the supported CLI read
path for ken's first-class `notes` table; on older ken `ken show` is absent
and resolution degrades gracefully to a compatibility fallback that reads
the same first-class `notes` data via direct SQL against ken's internal
schema from outside the tool), or finally the title. Unresolvable references are skipped with a
warning in `site/build.log` (the build never crashes). Cross-links between published
notes resolve to their generated pages; links to **unpublished** notes
degrade to plain text so unpublished content is never leaked.

**Regeneration is atomic.** `ongo-site` builds the new tree in a sibling
temp directory and then swaps it into place with a single `os.replace`
(same filesystem — a true atomic rename, not a copy). A reader that hits
the site mid-regeneration always sees a **complete** tree (the old site or
the new one, never a partial mix), so the running `ongo-serve` /
`http.server` **does not need to be restarted** across regenerations and
there is no read-during-write race. If the build fails or is interrupted,
the temp dir is removed (no `.tmp`/`.old` is left behind) and the
previously published site stays in place untouched.

## 3. Serve the site

```bash
bin/ongo-serve                                   # ./site on 0.0.0.0:80
bin/ongo-serve --dir /opt/ongo/site --port 80
```

For production, run it under systemd:

- Install the templated unit `deploy/ongo-site.service` (edit paths/user
  first). It binds `ongo-serve` directly to `0.0.0.0:80`.
- **Port 80 is privileged (<1024).** The unit grants the unprivileged
  `ongo` user `CAP_NET_BIND_SERVICE` (via `AmbientCapabilities`, which
  works even with `NoNewPrivileges=true` because systemd applies ambient
  capabilities before exec) — so the service binds :80 **without running
  as full root**. No reverse proxy is required for plain HTTP.

A reverse proxy is now **optional** — only needed if you also want HTTPS
on :443. If so, terminate TLS in nginx/caddy and proxy to the ongo-serve
backend (point it at a high local port instead of :80 in that case).

nginx TLS example (optional — ongo-serve on a local port, proxy adds 443):

```nginx
server {
    listen 443 ssl;
    server_name ongo.ergodic.xyz;
    # ssl_certificate / ssl_certificate_key ...
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

Caddy equivalent (`Caddyfile`, auto-TLS):

```
ongo.ergodic.xyz {
    reverse_proxy 127.0.0.1:80
}
```

## 4. DNS — manual, user-owned step

Hosting is **self-served on the user's own server**. Pointing the domain at
that server is a **manual step the user performs** — the ongo skill never
performs DNS changes or deploys, and contains no DigitalOcean (or other
registrar) credentials.

To go live, the user:

1. Generates the site (`bin/ongo-site`) and serves it (`bin/ongo-serve`,
   ideally via the systemd unit + reverse proxy above).
2. Manually creates a DNS **A record** for `ongo.ergodic.xyz` pointing at
   the server's public IP, at their DNS provider.
3. (Optional) Obtains a TLS certificate (e.g. caddy auto-HTTPS, or certbot
   for nginx).

That is the entire deployment boundary: ongo generates and can self-serve;
the user owns DNS and the server.
