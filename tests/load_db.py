import asyncio, json, statistics, time, httpx

BASE = 'http://127.0.0.1:8123'
RESUME = 'QA engineer, 4 years, Selenium, API testing, SQL, Agile. ' * 3

def stats(rows):
    if not rows:
        return {'n': 0}
    lat = [r[0] for r in rows]
    codes = {}
    for _, s in rows:
        codes[str(s)] = codes.get(str(s), 0) + 1
    return {'n': len(rows), 'p50_ms': round(statistics.median(lat) * 1000, 1),
            'p95_ms': round(sorted(lat)[min(int(len(lat) * .95), len(lat) - 1)] * 1000, 1),
            'max_ms': round(max(lat) * 1000, 1), 'status_codes': codes}

async def main():
    limits = httpx.Limits(max_connections=60)
    async with httpx.AsyncClient(base_url=BASE, timeout=60, limits=limits) as c, httpx.AsyncClient(base_url=BASE, timeout=60, limits=limits) as guest:
        r = await c.post('/api/auth/register', json={'email': f'load{int(time.time())}@example.com', 'password': 'load-test-pass-1', 'agree': True, 'age18': True, 'website': '', 'role': 'candidate'})
        print('register:', r.status_code, r.text[:120] if r.status_code != 200 else 'ok')
        cookie = r.cookies

        async def timed(fn):
            t = time.perf_counter()
            try:
                resp = await fn()
                return (time.perf_counter() - t, resp.status_code)
            except Exception:
                return (time.perf_counter() - t, 0)

        async def session_create():
            return await guest.post('/api/session', json={'resume': RESUME, 'role': 'QA Engineer', 'jd': '', 'country': 'India', 'level': 'mid', 'followups': False, 'count': 5})

        # probe single create
        p = await session_create()
        print('single create:', p.status_code, p.text[:100])
        if p.status_code != 200:
            return

        # 40 concurrent creates (DB writes)
        t0 = time.perf_counter()
        creates = await asyncio.gather(*[timed(session_create) for _ in range(40)])
        create_wall = time.perf_counter() - t0

        # sids for read tests: serial small wave
        sids = []
        for _ in range(8):
            x = await session_create()
            if x.status_code == 200:
                sids.append(x.json()['session_id'])
            await asyncio.sleep(0.2)
        print('captured sids:', len(sids))

        async def state_read(sid):
            return await guest.get(f'/api/session/{sid}/state')
        reads = []
        if sids:
            want = (sids * 30)[:200]
            t0 = time.perf_counter()
            for i in range(0, len(want), 50):
                reads += await asyncio.gather(*[timed(lambda s=s: state_read(s)) for s in want[i:i+50]])
            read_wall = time.perf_counter() - t0
        else:
            read_wall = 0

        async def hist():
            return await c.get('/api/history', cookies=cookie)
        t0 = time.perf_counter()
        hists = []
        for i in range(0, 100, 50):
            hists += await asyncio.gather(*[timed(hist) for _ in range(50)])
        hist_wall = time.perf_counter() - t0

        out = {
            'note': 'local SQLite, single worker; production is managed Postgres on Render - shape only, not capacity proof',
            'session_create_40_concurrent': {**stats(creates), 'wall_s': round(create_wall, 2)},
            'session_state_200_at_50': {**stats(reads), 'wall_s': round(read_wall, 2)},
            'history_100_at_50': {**stats(hists), 'wall_s': round(hist_wall, 2)},
            'websockets': 'none - app has no websocket endpoints; nothing to load-test',
        }
        print(json.dumps(out, indent=1))
        with open('/tmp/load-db.json', 'w') as f:
            json.dump(out, f, indent=1)

asyncio.run(main())
