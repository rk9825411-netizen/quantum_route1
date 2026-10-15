(() => {
  const $ = (selector) => document.querySelector(selector);
  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
  let roads = [];
  let locations = [];
  let selectedRegion = 'pune';

  async function getJson(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
    return data;
  }

  function renderRoads() {
    $('#road-count').textContent = `${roads.length} LINKS`;
    $('#road-list').innerHTML = roads.map((road) => `<li><span class="road-name"><strong>${escapeHtml(road.name)}</strong><small>${escapeHtml(road.road_id)} · ${escapeHtml(road.source)}</small></span><span class="status-label ${escapeHtml(road.status)}">${escapeHtml(road.status)}</span></li>`).join('');
    $('#admin-road').innerHTML = roads.map((road) => `<option value="${escapeHtml(road.road_id)}">${escapeHtml(road.road_id)} · ${escapeHtml(road.name)}</option>`).join('');
    const latestUpdate = roads.reduce((latest, road) => Math.max(latest, Date.parse(road.updated_at) || 0), 0);
    $('#updated-at').textContent = latestUpdate ? `Data as of ${new Date(latestUpdate).toLocaleString()}` : 'Data timestamp unavailable';
    window.QuantumMap.renderRoads(roads);
  }

  function renderLocations(shelters) {
    const options = locations.map((location) => `<option value="${escapeHtml(location.id)}">${escapeHtml(location.name)}</option>`).join('');
    const shelterOptions = shelters.map((shelter) => {
      const nearest = locations.reduce((best, location) => {
        const distance = (location.lat - shelter.lat) ** 2 + (location.lon - shelter.lon) ** 2;
        return distance < best.distance ? { location, distance } : best;
      }, { location: locations[0], distance: Infinity }).location;
      return `<option value="${escapeHtml(nearest.id)}">${escapeHtml(shelter.name)}</option>`;
    }).join('');
    $('#start').innerHTML = options;
    $('#destination').innerHTML = `<optgroup label="Road network">${options}</optgroup><optgroup label="Emergency shelters">${shelterOptions}</optgroup>`;
    $('#start').value = locations[0]?.id || '';
    $('#destination').value = locations[locations.length - 1]?.id || '';
  }

  function renderAlerts(alerts) {
    $('#alert-list').innerHTML = alerts.map((alert) => `<li><span class="severity">${escapeHtml(alert.severity)} · ${escapeHtml(alert.source)}</span><strong>${escapeHtml(alert.affected_area)}</strong>${escapeHtml(alert.message)}<br><small>${escapeHtml(new Date(alert.updated_at).toLocaleString())}</small></li>`).join('');
  }

  function renderShelters(shelters) {
    $('#shelter-list').innerHTML = shelters.map((shelter) => `<li><span class="shelter-status">${escapeHtml(shelter.availability)}</span><strong>${escapeHtml(shelter.name)}</strong><small>${escapeHtml(shelter.capacity)} places · ${escapeHtml(shelter.source)}</small></li>`).join('');
    window.QuantumMap.renderShelters(shelters);
  }

  $('#route-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const result = $('#route-result');
    result.classList.remove('error');
    result.textContent = 'Calculating route...';
    try {
      const route = await getJson('/api/route/calculate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ region_id: selectedRegion, start: $('#start').value, destination: $('#destination').value }) });
      result.innerHTML = `<strong>${escapeHtml(route.distance_km)} km · about ${escapeHtml(route.estimated_minutes)} min</strong><br>${escapeHtml(route.selection_reason)}${route.warnings.map((warning) => `<span class="warning">${escapeHtml(warning)}</span>`).join('')}`;
      window.QuantumMap.renderRoute(route, locations);
    } catch (error) {
      result.classList.add('error');
      result.textContent = error.message;
    }
  });

  $('#admin-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = $('#admin-message');
    message.textContent = 'Saving...';
    try {
      const response = await getJson('/api/admin/roads/status', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Admin-Token': $('#admin-token').value },
        body: JSON.stringify({ road_id: $('#admin-road').value, status: $('#admin-status').value, reason: $('#admin-reason').value, source: 'Manual demo update' })
      });
      roads = roads.map((road) => road.road_id === response.road.road_id ? response.road : road);
      renderRoads();
      message.textContent = 'Saved. Recalculate the route to see the change.';
    } catch (error) {
      message.textContent = error.message;
    }
  });

  async function loadRegion(region) {
    selectedRegion = region.region_id;
    $('#map-region').textContent = `${region.city_name} · ${region.state_name}`;
    window.QuantumMap.setCenter(region);
    const query = `?region_id=${encodeURIComponent(selectedRegion)}`;
    const [roadData, locationData, alertData, shelterData] = await Promise.all([
      getJson(`/api/roads${query}`), getJson(`/api/locations${query}`), getJson(`/api/alerts${query}`), getJson(`/api/shelters${query}`)
    ]);
    roads = roadData.roads;
    locations = locationData.locations;
    renderRoads();
    renderLocations(shelterData.shelters);
    renderAlerts(alertData.alerts);
    renderShelters(shelterData.shelters);
    $('#route-form').requestSubmit();
  }

  $('#region').addEventListener('change', async (event) => {
    const region = JSON.parse(event.target.selectedOptions[0].dataset.region);
    const result = $('#route-result');
    result.classList.remove('error');
    result.textContent = 'Loading demo network...';
    try {
      await loadRegion(region);
    } catch (error) {
      result.classList.add('error');
      result.textContent = `Could not load this region: ${error.message}`;
    }
  });

  async function loadDashboard() {
    try {
      const data = await getJson('/api/regions');
      $('#region').innerHTML = data.regions.map((region) => `<option value="${escapeHtml(region.region_id)}" data-region="${escapeHtml(JSON.stringify(region))}">${escapeHtml(region.state_name)} · ${escapeHtml(region.city_name)}</option>`).join('');
      const region = data.regions.find((item) => item.region_id === 'pune') || data.regions[0];
      $('#region').value = region.region_id;
      await loadRegion(region);
    } catch (error) {
      $('#route-result').classList.add('error');
      $('#route-result').textContent = `Could not load dashboard data: ${error.message}`;
    }
  }

  loadDashboard();
})();
