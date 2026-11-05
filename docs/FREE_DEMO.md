# Free demo sharing

The supported free option is Docker Compose on the developer's computer. It
keeps the database, uploaded PDFs, Java/Audiveris, and Poppler inside Docker;
the host only needs Docker Desktop. It does not create a Google Cloud resource
or require a billing account.

For a temporary HTTPS link, use Cloudflare Quick Tunnel through the optional
Compose overlay:

```bash
docker compose -f compose.yaml -f compose.free-demo.yaml \
  --profile tunnel up --build --wait
docker compose logs -f tunnel
```

Cloudflare prints a random `https://…trycloudflare.com` URL. Share that URL only
with the intended tester. The currently verified demo URL is
`https://locate-valuation-using-donald.trycloudflare.com` while its container is
running; a restart generates a different URL. Quick Tunnels are free and require
no Cloudflare account or domain, but the URL changes whenever the tunnel restarts
and stops when the tunnel container stops. Cloudflare documents them for testing and
development, with a 200 in-flight-request limit and no uptime guarantee:
[Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

Stop the demo and preserve the Docker library with:

```bash
docker compose -f compose.yaml -f compose.free-demo.yaml \
  --profile tunnel down
```

Do not add `--volumes`; that would remove the Docker database and uploaded
files. The temporary tunnel is not a production deployment: it depends on this
computer, has no stable hostname, and the default demo profile selector is for
local testing. For a private class walkthrough, use the local URL instead or
add Cloudflare's documented `--allowed-mail` restriction to a separately run
`cloudflared` command.

The paid Google VM, Cloud Run, managed database, persistent public tunnel, and
other billable hosting paths are intentionally out of scope for the free-only
launch. The temporary URL above is demo evidence, not a permanent deployment.
