(() => {
  const colors = { open: '#18835f', blocked: '#c44d40', risky: '#d88930', unknown: '#87918c' };
  let map;
  let roadLayers = [];
  let routeLayer;
  let markersLayer;

  function initialize() {
    const message = document.getElementById('map-message');
    if (!window.L) {
      message.textContent = 'Map library unavailable. Road statuses and route calculations remain available in the panels.';
      return false;
    }
    map = L.map('map', { zoomControl: false }).setView([18.521, 73.855], 13);
    L.control.zoom({ position: 'bottomright' }).addTo(map);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' })
      .addTo(map).on('tileerror', () => {
        message.textContent = 'Street basemap is unavailable. Check your internet connection; road data remains local.';
        message.classList.remove('hidden');
      }).on('tileload', () => message.classList.add('hidden'));
    markersLayer = L.layerGroup().addTo(map);
    return true;
  }

  function renderRoads(roads) {
    if (!map && !initialize()) return;
    roadLayers.forEach((layer) => map.removeLayer(layer));
    roadLayers = roads.map((road) => L.polyline([[road.from_lat, road.from_lon], [road.to_lat, road.to_lon]], {
      color: colors[road.status], weight: 6, opacity: 0.82
    }).bindTooltip(`${road.name} · ${road.status.toUpperCase()}`).addTo(map));
  }

  function renderShelters(shelters) {
    if (!map && !initialize()) return;
    shelters.forEach((shelter) => L.circleMarker([shelter.lat, shelter.lon], { radius: 7, color: '#fff', weight: 2, fillColor: '#176b89', fillOpacity: 1 })
      .bindTooltip(`${shelter.name} · ${shelter.availability} · DEMO`).addTo(markersLayer));
  }

  function renderRoute(route, locations) {
    if (!map && !initialize()) return;
    if (routeLayer) map.removeLayer(routeLayer);
    markersLayer.clearLayers();
    routeLayer = L.polyline(route.coordinates, { color: '#176b89', weight: 8, opacity: 0.95 }).addTo(map);
    const start = locations.find((item) => item.id === route.nodes[0]);
    const end = locations.find((item) => item.id === route.nodes[route.nodes.length - 1]);
    if (start) L.marker([start.lat, start.lon]).bindTooltip(`START · ${start.name}`).addTo(markersLayer);
    if (end) L.marker([end.lat, end.lon]).bindTooltip(`DESTINATION · ${end.name}`).addTo(markersLayer);
    map.fitBounds(routeLayer.getBounds(), { padding: [35, 35] });
  }

  window.QuantumMap = { renderRoads, renderShelters, renderRoute };
})();
