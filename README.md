# QuantumRoute

Software-only evacuation route-planning demo: Flask API, SQLite status database, NetworkX routing, and a Leaflet/OpenStreetMap dashboard. It needs no hardware or paid API key.

The state/city selector includes simulated networks for Pune (Maharashtra), Patna (Bihar), Lucknow (Uttar Pradesh), and Kolkata (West Bengal). Each selection has its own demo roads, notices, shelters, and isolated route graph.

**Safety/data limits:** road statuses, alerts, and shelters are simulated demo records, not current real-world reports or safety advice. Unknown roads are not confirmed safe. The local API and graph work without internet; Leaflet, fonts, and OpenStreetMap basemap tiles need internet.

## Run on macOS

In VS Code, open the `quantum-route` folder and run these commands in its Terminal:

```sh
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open http://127.0.0.1:5000. SQLite and sample records are initialized automatically on first run. The demo admin token is `demo-admin-token`; edit `.env` to change it and restart. This token is basic demo protection only, not production authentication.

## Try the demo

- Old Market to South Hub routes around the blocked Lowland Cut-through.
- Expand **Update demo road status**, enter the admin token, change a status, and calculate again.
- Run `python -m pytest` in the activated virtual environment.

## API

- `GET /api/regions` lists available demo networks.
- `GET /api/roads`, `/api/locations`, `/api/alerts`, `/api/shelters` accept optional `?region_id=bihar` (defaults to `pune`).
- `POST /api/route/calculate` accepts `{"region_id":"bihar","start":"patna_central","destination":"patna_south"}`.
- `POST /api/admin/roads/status` requires `X-Admin-Token`; JSON fields: `road_id`, `status` (`open`, `blocked`, `risky`, or `unknown`), `reason`, optional `source`.

Routing excludes blocked roads and uses distance weights with configurable penalties (2.5x risky, 1.4x unknown). Time estimates use sample speeds. There is no live traffic or verified road feed. An external routing provider can add geometry/directions, but does not inherently know closures or flood risk.
# QuantumRoute

Software-only evacuation route-planning demo: Flask API, SQLite status database, NetworkX routing, and a Leaflet/OpenStreetMap dashboard. It needs no hardware or paid API key.

**Safety/data limits:** road statuses, alerts, and shelters are simulated demo records, not current real-world reports or safety advice. Unknown roads are not confirmed safe. The local API and graph work without internet; Leaflet, fonts, and OpenStreetMap basemap tiles need internet.

## Run on macOS

In VS Code, open the `quantum-route` folder and run these commands in its Terminal:

```sh
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open http://127.0.0.1:5000. SQLite and sample records are initialized automatically on first run. The demo admin token is `demo-admin-token`; edit `.env` to change it and restart. This token is basic demo protection only, not production authentication.

## Try the demo

- Old Market to South Hub routes around the blocked Lowland Cut-through.
- Expand **Update demo road status**, enter the admin token, change a status, and calculate again.
- Run `pytest` in the activated virtual environment.

## API

- `GET /api/roads`, `/api/locations`, `/api/alerts`, `/api/shelters`
- `POST /api/route/calculate` JSON: `{"start":"old_market","destination":"south_hub"}`
- `POST /api/admin/roads/status` requires `X-Admin-Token`; JSON fields: `road_id`, `status` (`open`, `blocked`, `risky`, or `unknown`), `reason`, optional `source`.

Routing excludes blocked roads and uses distance weights with configurable penalties (2.5x risky, 1.4x unknown). Time estimates use sample speeds. There is no live traffic or verified road feed. An external routing provider can add geometry/directions, but does not inherently know closures or flood risk.
