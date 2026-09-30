/**
 * Viaggio Italia — Local Travel Planner & AI Concierge
 * Frontend Application Controller
 */

class ViaggioApp {
  constructor() {
    this.currentTrip = null;
    this.currentCity = 'sorrento';
    this.selectedLLM = 'auto';
    this.activeDayIndex = 0;
    this.activeTab = 'tab-home';
    this.places = [];
    this.restaurants = [];
    this.dishes = [];
    this.map = null;
    this.markers = [];
    this.polylines = [];

    this.mcpSampleArgs = {
      search_places: { query: 'Piazza Tasso', city_or_region: 'sorrento', category: 'all' },
      search_nearby_places: { latitude: 40.6263, longitude: 14.3758, radius_meters: 1500 },
      get_place_details: { place_name: 'Pompeii Archaeological Park', city_or_region: 'sorrento' },
      search_restaurants: { city_or_region: 'sorrento', vegetarian_only: true, max_price_tier: 2 },
      calculate_route: { origin: 'Sorrento Historical Center', destination: 'Marina Grande Sorrento', travel_mode: 'walking' },
      compare_routes: { origin: 'Sorrento', destination: 'Pompeii Archaeological Park' },
      calculate_multi_stop_route: { origin: 'Piazza Tasso', destinations: ['Villa Comunale Park', 'Marina Grande', 'Piazza Tasso'], travel_mode: 'walking' },
      calculate_route_matrix: { origins: ['Piazza Tasso', 'Marina Grande'], destinations: ['Bagni della Regina Giovanna', 'Vallone dei Mulini'], travel_mode: 'walking' },
      get_maps_url: { destination: 'Piazza Tasso', city_or_region: 'Sorrento' }
    };
  }

  async init() {
    this.bindEvents();
    this.initMap();

    const savedTripStr = localStorage.getItem('viaggio_active_trip');
    let loadedTrip = null;
    if (savedTripStr) {
      try {
        const parsed = JSON.parse(savedTripStr);
        if (parsed && Array.isArray(parsed.days) && parsed.days.length > 0) {
          loadedTrip = parsed;
        }
      } catch (e) {
        console.warn('LocalStorage parse error:', e);
      }
    }

    if (loadedTrip) {
      this.currentTrip = loadedTrip;
      this.currentCity = loadedTrip.destination || 'sorrento';
      const globalSelect = document.getElementById('global-dest-select');
      if (globalSelect) globalSelect.value = this.currentCity;
      const formDest = document.getElementById('form-destination');
      if (formDest) formDest.value = this.currentCity;
      await this.loadExploreData();
      this.renderItineraryView();
      this.renderSelectionsView();
    } else {
      await this.loadPreset('sorrento');
    }
  }

  bindEvents() {
    // Nav Tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const targetTab = e.currentTarget.getAttribute('data-tab');
        this.switchToTab(targetTab);
      });
    });

    // Global LLM Engine Selector
    const llmSelect = document.getElementById('global-llm-select');
    if (llmSelect) {
      llmSelect.addEventListener('change', (e) => {
        this.selectedLLM = e.target.value;
      });
    }

    // Global Destination Selector
    const globalSelect = document.getElementById('global-dest-select');
    if (globalSelect) {
      globalSelect.addEventListener('change', async (e) => {
        const newCity = e.target.value;
        await this.loadPreset(newCity);
      });
    }

    // Explore Category Chips
    document.querySelectorAll('.category-chips .chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        document.querySelectorAll('.category-chips .chip').forEach(c => c.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const cat = e.currentTarget.getAttribute('data-category');
        this.renderExplorePlaces(cat);
      });
    });

    // Explore Search
    const searchBtn = document.getElementById('explore-search-btn');
    const searchInput = document.getElementById('explore-search-input');
    if (searchBtn && searchInput) {
      searchBtn.addEventListener('click', () => this.filterExplorePlaces(searchInput.value));
      searchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') this.filterExplorePlaces(searchInput.value);
      });
    }

    // Plan Trip Form Submit
    const form = document.getElementById('trip-planner-form');
    if (form) {
      form.addEventListener('submit', (e) => this.handleGenerateTrip(e));
    }

    // MCP Modal Open/Close
    const mcpOpenBtn = document.getElementById('open-mcp-modal-btn');
    const mcpCloseBtn = document.getElementById('close-mcp-modal-btn');
    const mcpModal = document.getElementById('mcp-modal');
    if (mcpOpenBtn && mcpModal) {
      mcpOpenBtn.addEventListener('click', () => {
        mcpModal.classList.add('open');
        mcpModal.classList.add('active');
      });
    }
    if (mcpCloseBtn && mcpModal) {
      mcpCloseBtn.addEventListener('click', () => {
        mcpModal.classList.remove('open');
        mcpModal.classList.remove('active');
      });
    }

    // MCP Tool Selector Change
    const mcpSelect = document.getElementById('mcp-tool-select');
    const mcpArgsArea = document.getElementById('mcp-args-json');
    if (mcpSelect && mcpArgsArea) {
      mcpSelect.addEventListener('change', (e) => {
        const tool = e.target.value;
        const sample = this.mcpSampleArgs[tool] || {};
        mcpArgsArea.value = JSON.stringify(sample, null, 2);
      });
    }

    // MCP Execute Button
    const mcpRunBtn = document.getElementById('mcp-run-tool-btn');
    if (mcpRunBtn) {
      mcpRunBtn.addEventListener('click', () => this.handleRunMcpTool());
    }

    // AI Drawer Open/Close
    const chatOpenBtn = document.getElementById('open-chat-drawer-btn');
    const chatCloseBtn = document.getElementById('close-chat-drawer-btn');
    const chatDrawer = document.getElementById('chat-drawer');
    const drawerBackdrop = document.getElementById('drawer-backdrop');

    if (chatOpenBtn && chatDrawer) {
      chatOpenBtn.addEventListener('click', () => {
        chatDrawer.classList.add('open');
        drawerBackdrop.classList.add('open');
      });
    }
    const closeDrawer = () => {
      chatDrawer.classList.remove('open');
      drawerBackdrop.classList.remove('open');
    };
    if (chatCloseBtn) chatCloseBtn.addEventListener('click', closeDrawer);
    if (drawerBackdrop) drawerBackdrop.addEventListener('click', closeDrawer);

    // AI Chat Send
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatInput = document.getElementById('chat-input-text');
    if (chatSendBtn && chatInput) {
      chatSendBtn.addEventListener('click', () => this.handleSendChat());
      chatInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') this.handleSendChat();
      });
    }
  }

  switchToTab(tabId) {
    document.querySelectorAll('.nav-tab').forEach(t => {
      t.classList.toggle('active', t.getAttribute('data-tab') === tabId);
    });
    document.querySelectorAll('.tab-content').forEach(c => {
      c.classList.toggle('active', c.id === tabId);
    });
    this.activeTab = tabId;

    if (tabId === 'tab-itinerary') {
      setTimeout(() => {
        if (this.map) {
          this.map.invalidateSize();
          this.renderMapForActiveDay();
        }
      }, 150);
    }
  }

  // Map Initialization & Rendering (Leaflet)
  initMap() {
    const mapEl = document.getElementById('map-canvas');
    if (!mapEl) return;

    if (this.map) {
      try { this.map.remove(); } catch (e) {}
    }

    this.map = L.map('map-canvas', {
      zoomControl: true,
      scrollWheelZoom: true
    }).setView([40.6263, 14.3758], 13);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(this.map);
  }

  renderMapForActiveDay() {
    if (!this.map || !this.currentTrip || !this.currentTrip.days) return;

    const day = this.currentTrip.days[this.activeDayIndex];
    if (!day || !day.stops) return;

    // Clear existing markers and polylines
    this.markers.forEach(m => this.map.removeLayer(m));
    this.polylines.forEach(p => this.map.removeLayer(p));
    this.markers = [];
    this.polylines = [];

    const latLngs = [];
    // Only map stops selected by the user for this day
    const activeStops = day.stops.filter(stop => stop.selected !== false);

    activeStops.forEach((stop, idx) => {
      if (!stop.latitude || !stop.longitude) return;

      const isFood = (stop.type === 'restaurant' || stop.type === 'lunch' || stop.type === 'dinner' || stop.category === 'food');
      const isHotel = (stop.type === 'hotel' || stop.category === 'hotel');
      
      const bgColor = isFood ? '#3A5A40' : (isHotel ? '#1B3B6F' : '#C85A32');
      const iconLetter = isFood ? '🍴' : (isHotel ? '🏨' : String(idx + 1));

      const customIcon = L.divIcon({
        className: 'custom-map-pin',
        html: `<div style="background-color:${bgColor}; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:bold; font-size:12px; border:2px solid #ffffff; box-shadow:0 3px 6px rgba(0,0,0,0.3); cursor:pointer;">${iconLetter}</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14]
      });

      const marker = L.marker([stop.latitude, stop.longitude], { icon: customIcon }).addTo(this.map);
      const photosUrl = stop.google_photos_url || stop.googlePhotosUrl || stop.maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(stop.name)}`;
      
      const popupContent = `
        <div style="font-family: inherit; padding: 4px;">
          <strong style="font-size: 14px; color: #1B3B6F;">${stop.name}</strong>
          <p style="margin: 4px 0; font-size: 12px; color: #666;">${stop.time_slot || ''} · ${stop.category || stop.type}</p>
          ${stop.notes ? `<p style="font-size: 11px; margin: 4px 0 6px;">${stop.notes}</p>` : ''}
          <a href="${photosUrl}" target="_blank" style="display:inline-block; font-size:11px; color:#C85A32; font-weight:bold; text-decoration:none;">📸 View Photos & Reviews on Google Maps ↗</a>
        </div>
      `;
      marker.bindPopup(popupContent);
      this.markers.push(marker);
      latLngs.push([stop.latitude, stop.longitude]);
    });

    // Draw route polyline
    if (latLngs.length > 1) {
      const polyline = L.polyline(latLngs, {
        color: '#C85A32',
        weight: 3,
        opacity: 0.8,
        dashArray: '6, 8'
      }).addTo(this.map);
      this.polylines.push(polyline);
      this.map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
    } else if (latLngs.length === 1) {
      this.map.setView(latLngs[0], 14);
    }
  }

  // Data Loaders
  async loadExploreData() {
    try {
      const res = await fetch(`/api/explore?city=${this.currentCity}`);
      if (!res.ok) throw new Error('Failed to load places');
      const data = await res.json();
      this.places = data.places || [];
      this.renderExplorePlaces('all');
    } catch (err) {
      console.error('Error fetching explore places:', err);
    }
  }

  getCategoryBadge(category) {
    const cat = (category || 'sight').toLowerCase();
    const map = {
      'historical': { label: 'Ancient History', icon: '🏛️', cls: 'badge-historical' },
      'museums': { label: 'Art & Museum', icon: '🎨', cls: 'badge-museums' },
      'churches': { label: 'Sacred & Religious', icon: '⛪', cls: 'badge-churches' },
      'viewpoints': { label: 'Panoramic Sunset & View', icon: '🌅', cls: 'badge-viewpoints' },
      'beaches': { label: 'Beach & Coastal Lagoon', icon: '🏖️', cls: 'badge-beaches' },
      'shopping': { label: 'Artisan Crafts & Fashion', icon: '🛍️', cls: 'badge-shopping' },
      'food': { label: 'Historic Dining & Gelato', icon: '🍕', cls: 'badge-food' },
      'lunch': { label: 'Lunch Trattoria', icon: '🍴', cls: 'badge-dining' },
      'dinner': { label: 'Dinner & Passeggiata', icon: '🍷', cls: 'badge-dining' },
      'restaurant': { label: 'Trattoria & Dining', icon: '🍴', cls: 'badge-dining' }
    };
    const item = map[cat] || { label: (category || 'Sight').toUpperCase(), icon: '📍', cls: 'badge-sight' };
    return `<span class="stop-badge ${item.cls}">${item.icon} ${item.label}</span>`;
  }

  renderWhatToDo(whatToDoList) {
    if (!Array.isArray(whatToDoList) || whatToDoList.length === 0) return '';
    return `
      <div class="stop-what-to-do">
        <div class="what-to-do-title">🎯 What To Do There:</div>
        <ul class="what-to-do-list">
          ${whatToDoList.map(step => `<li class="what-to-do-item">${step}</li>`).join('')}
        </ul>
      </div>
    `;
  }

  renderExplorePlaces(category = 'all') {
    const grid = document.getElementById('explore-places-grid');
    if (!grid) return;

    let filtered = this.places;
    if (category !== 'all') {
      filtered = this.places.filter(p => p.category === category);
    }

    if (filtered.length === 0) {
      grid.innerHTML = '<div class="empty-state">No places found in this category.</div>';
      return;
    }

    grid.innerHTML = filtered.map(place => {
      const urgency = (place.ticket_urgency || place.booking_urgency || place.bookingUrgency || 'flexible').toLowerCase();
      const urgencyClass = urgency === 'urgent' ? 'urgency-urgent' : (urgency === 'advance' ? 'urgency-advance' : 'urgency-flexible');
      const urgencyLabel = urgency === 'urgent' ? '🔴 High Urgency' : (urgency === 'advance' ? '🟡 Advance Booking' : '🟢 Flexible / Walk-in');
      const ticketUrl = place.ticket_url || place.official_booking_url || place.officialBookingUrl || '';
      const mapsUrl = place.google_maps_url || place.maps_url || place.googleMapsUrl || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name + ', ' + (place.city || 'Italy') + ', Italy')}`;
      const photosUrl = place.google_photos_url || place.googlePhotosUrl || mapsUrl;
      const imageUrl = place.image_url || place.imageUrl || 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80';
      const dwell = place.dwell_time_hours || (place.typicalDwellMinutes ? (place.typicalDwellMinutes / 60.0).toFixed(1) : (place.typical_dwell_minutes ? (place.typical_dwell_minutes / 60.0).toFixed(1) : 1.5));
      const hoursText = place.opening_hours ? (typeof place.opening_hours === 'object' ? Object.values(place.opening_hours)[0] : place.opening_hours) : 'Open daily / Check official schedule';
      const safeName = (place.name || 'Place').replace(/'/g, "\\'");

      return `
        <div class="place-card">
          <div class="place-card-banner" onclick="app.openPhotoLightbox('${safeName}', '${imageUrl}', '${photosUrl}')" title="Click to view full photo">
            <img src="${imageUrl}" alt="${place.name}" class="place-banner-img" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80'">
            <div class="photo-overlay-tag">📸 View Landmark Photo</div>
          </div>
          <div class="place-card-body">
            <div class="place-card-header">
              <div>
                <a href="${photosUrl}" target="_blank" class="place-title-link" title="Open Google Maps & Photos">
                  <h4 class="place-name">${place.name} <span class="external-icon">↗</span></h4>
                </a>
                <div class="place-category-row">
                  ${this.getCategoryBadge(place.category)}
                </div>
              </div>
              <span class="place-rating">⭐ ${place.rating || 4.8}</span>
            </div>
            <p class="place-address">📍 ${place.address || 'Italy'}</p>
            <div class="place-meta-pills">
              <span class="meta-pill">⏱️ ${dwell}h visit</span>
              <span class="meta-pill ${urgencyClass}">${urgencyLabel}</span>
            </div>
            <p class="place-description">${place.description || ''}</p>
            ${this.renderWhatToDo(place.what_to_do)}
            <div class="place-hours">
              <strong>🕒 Hours:</strong> ${hoursText}
            </div>
            <div class="place-card-footer">
              <a href="${photosUrl}" target="_blank" class="btn btn-sm btn-primary">📸 Google Maps & Photos ↗</a>
              ${ticketUrl ? `<a href="${ticketUrl}" target="_blank" class="btn btn-sm btn-outline">🎟️ Official Tickets</a>` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  filterExplorePlaces(query) {
    if (!query) {
      this.renderExplorePlaces('all');
      return;
    }
    const q = query.toLowerCase();
    const grid = document.getElementById('explore-places-grid');
    if (!grid) return;

    const filtered = this.places.filter(p => 
      (p.name && p.name.toLowerCase().includes(q)) || 
      (p.description && p.description.toLowerCase().includes(q)) ||
      (p.category && p.category.toLowerCase().includes(q)) ||
      (p.address && p.address.toLowerCase().includes(q))
    );

    if (filtered.length === 0) {
      grid.innerHTML = `<div class="empty-state">No places matching "${query}".</div>`;
      return;
    }

    grid.innerHTML = filtered.map(place => {
      const ticketUrl = place.ticket_url || place.official_booking_url || place.officialBookingUrl || '';
      const mapsUrl = place.google_maps_url || place.maps_url || place.googleMapsUrl || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name + ', ' + (place.city || 'Italy') + ', Italy')}`;
      const photosUrl = place.google_photos_url || place.googlePhotosUrl || mapsUrl;
      const imageUrl = place.image_url || place.imageUrl || 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80';
      const safeName = (place.name || 'Place').replace(/'/g, "\\'");

      return `
        <div class="place-card">
          <div class="place-card-banner" onclick="app.openPhotoLightbox('${safeName}', '${imageUrl}', '${photosUrl}')">
            <img src="${imageUrl}" alt="${place.name}" class="place-banner-img" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80'">
            <div class="photo-overlay-tag">📸 View Landmark Photo</div>
          </div>
          <div class="place-card-body">
            <div class="place-card-header">
              <div>
                <a href="${photosUrl}" target="_blank" class="place-title-link">
                  <h4 class="place-name">${place.name} <span class="external-icon">↗</span></h4>
                </a>
                <div class="place-category-row">
                  ${this.getCategoryBadge(place.category)}
                </div>
              </div>
              <span class="place-rating">⭐ ${place.rating || 4.8}</span>
            </div>
            <p class="place-address">📍 ${place.address || 'Italy'}</p>
            <p class="place-description">${place.description || ''}</p>
            ${this.renderWhatToDo(place.what_to_do)}
            <div class="place-card-footer">
              <a href="${photosUrl}" target="_blank" class="btn btn-sm btn-primary">📸 Google Maps & Photos ↗</a>
              ${ticketUrl ? `<a href="${ticketUrl}" target="_blank" class="btn btn-sm btn-outline">🎟️ Tickets</a>` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Presets & Trip Generator
  async loadPreset(cityKey) {
    this.currentCity = cityKey;
    const globalSelect = document.getElementById('global-dest-select');
    if (globalSelect) globalSelect.value = cityKey;
    const formDest = document.getElementById('form-destination');
    if (formDest) formDest.value = cityKey;

    await this.loadExploreData();

    const presetPayload = {
      destination: cityKey,
      duration_days: cityKey === 'puglia' ? 4 : (cityKey === 'milan' ? 2 : 3),
      pace: 'balanced',
      dietary_preference: 'vegetarian',
      interests: ['historical', 'museums', 'beaches', 'viewpoints', 'shopping'],
      llm_provider: this.selectedLLM || 'auto'
    };

    try {
      await this.generateTrip(presetPayload);
      this.switchToTab('tab-itinerary');
    } catch (err) {
      console.warn('Preset initial generation error:', err);
    }
  }

  async handleGenerateTrip(e) {
    e.preventDefault();
    const dest = document.getElementById('form-destination').value;
    const duration = parseInt(document.getElementById('form-duration').value, 10);
    const pace = document.getElementById('form-pace').value;
    const dietary = document.getElementById('form-dietary').value;
    const hotel = document.getElementById('form-hotel').value;

    const checkedInterests = Array.from(document.querySelectorAll('input[name="interests"]:checked')).map(cb => cb.value);

    const payload = {
      destination: dest,
      duration_days: duration,
      pace: pace,
      dietary_preference: dietary,
      hotel_name: hotel || undefined,
      interests: checkedInterests,
      llm_provider: this.selectedLLM || 'auto'
    };

    const submitBtn = document.getElementById('generate-trip-btn');
    if (submitBtn) {
      submitBtn.textContent = '⏳ Calculating Non-Backtracking Routes...';
      submitBtn.disabled = true;
    }

    try {
      await this.generateTrip(payload);
      this.switchToTab('tab-itinerary');
    } catch (err) {
      alert('Error generating itinerary: ' + (err.message || 'Please check server connection'));
    } finally {
      if (submitBtn) {
        submitBtn.textContent = '🚀 Generate Optimized Itinerary';
        submitBtn.disabled = false;
      }
    }
  }

  async generateTrip(payload) {
    const res = await fetch('/api/trips/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      let errMsg = 'Trip generation failed';
      try {
        const err = await res.json();
        errMsg = err.error || err.detail || errMsg;
      } catch (e) {}
      throw new Error(errMsg);
    }

    const data = await res.json();
    this.currentTrip = data.trip || data;
    this.activeDayIndex = 0;
    try {
      localStorage.setItem('viaggio_active_trip', JSON.stringify(this.currentTrip));
    } catch (e) {
      console.warn('LocalStorage save skipped:', e);
    }
    this.renderItineraryView();
    this.renderSelectionsView();
  }

  renderItineraryView() {
    if (!this.currentTrip) return;

    const trip = this.currentTrip;
    const titleEl = document.getElementById('trip-title');
    const subtitleEl = document.getElementById('trip-subtitle');
    if (titleEl) titleEl.textContent = trip.title || `${trip.destination.toUpperCase()} Curated Journey`;
    if (subtitleEl) subtitleEl.textContent = `${trip.duration_days} Days · ${trip.pace.toUpperCase()} Pace · ${trip.dietary_preference.replace('_', ' ').toUpperCase()}`;

    // Render Day Tabs
    const tabsContainer = document.getElementById('day-tabs-container');
    if (tabsContainer && trip.days) {
      tabsContainer.innerHTML = trip.days.map((day, idx) => `
        <button class="day-tab-btn ${idx === this.activeDayIndex ? 'active' : ''}" onclick="app.setActiveDay(${idx})">
          📅 Day ${day.day_number || idx + 1}
        </button>
      `).join('');
    }

    this.renderActiveDayStops();
    this.renderMapForActiveDay();
  }

  setActiveDay(dayIndex) {
    this.activeDayIndex = dayIndex;
    document.querySelectorAll('.day-tab-btn').forEach((btn, idx) => {
      btn.classList.toggle('active', idx === dayIndex);
    });
    this.renderActiveDayStops();
    this.renderMapForActiveDay();
  }

  renderActiveDayStops() {
    if (!this.currentTrip || !this.currentTrip.days) return;
    const day = this.currentTrip.days[this.activeDayIndex];
    if (!day) return;

    // Filter selected stops to compute live pacing
    const selectedStops = (day.stops || []).filter(s => s.selected !== false);
    const selectedDwell = selectedStops.reduce((sum, s) => sum + (s.dwell_time_hours || 1.2), 0);
    const estTransitHours = Math.max(0.5, (selectedStops.length - 1) * 0.4);
    const activeHours = selectedStops.length > 0 ? (selectedDwell + estTransitHours) : 0;
    const estWalkingKm = Math.max(0.5, selectedStops.length * 0.9);

    const pacing = activeHours <= 6.5 ? 'comfortable' : (activeHours <= 8.5 ? 'busy' : 'overloaded');
    const statusClass = pacing === 'comfortable' ? 'status-comfortable' : (pacing === 'busy' ? 'status-busy' : 'status-overloaded');
    const statusIcon = pacing === 'comfortable' ? '🟢' : (pacing === 'busy' ? '🟡' : '🔴');
    const statusText = pacing.charAt(0).toUpperCase() + pacing.slice(1);

    // Update Pacing Bar
    const statusPill = document.getElementById('pacing-status-pill');
    const walkPill = document.getElementById('pacing-walk-pill');
    const themeEl = document.getElementById('active-day-theme');

    if (statusPill) {
      statusPill.className = `pacing-pill ${statusClass}`;
      statusPill.textContent = `${statusIcon} ${statusText} Day (${activeHours.toFixed(1)}h · ${selectedStops.length}/${(day.stops || []).length} Selected)`;
    }
    if (walkPill) {
      walkPill.textContent = `🚶 ${estWalkingKm.toFixed(1)} km Walking`;
    }
    if (themeEl) {
      themeEl.textContent = `Theme: ${day.theme || 'Authentic Discovery'}`;
    }

    // Render Timeline Stops
    const container = document.getElementById('timeline-stops-container');
    if (!container) return;

    if (!day.stops || day.stops.length === 0) {
      container.innerHTML = '<div class="empty-state">No scheduled stops for this day.</div>';
      return;
    }

    container.innerHTML = day.stops.map((stop, idx) => {
      const isSelected = stop.selected !== false;
      const isDining = stop.type === 'lunch' || stop.type === 'dinner' || stop.type === 'restaurant' || stop.category === 'food';
      const icon = isDining ? '🍴' : '🏛️';
      const imageUrl = stop.image_url || stop.imageUrl || 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80';

      let mapsUrl = stop.maps_url || stop.googleMapsUrl;
      if (!mapsUrl) {
        mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(stop.name + ', ' + (stop.city || this.currentCity || 'Italy') + ', Italy')}`;
      }
      const photosUrl = stop.google_photos_url || stop.googlePhotosUrl || mapsUrl;
      const safeName = (stop.name || 'Place').replace(/'/g, "\\'");

      return `
        <div class="timeline-stop-card ${isSelected ? 'stop-selected' : 'stop-deselected'}">
          <div class="stop-card-top-bar">
            <label class="stop-select-checkbox-label" title="Toggle whether this stop is in your active day itinerary">
              <input type="checkbox" class="stop-select-checkbox" ${isSelected ? 'checked' : ''} onchange="app.toggleStopSelection(${this.activeDayIndex}, ${idx}, this.checked)">
              <span class="stop-select-custom-box"></span>
              <span class="stop-select-label-text">${isSelected ? '✓ In My Day Plan' : '+ Add to Day Plan'}</span>
            </label>
            <span class="stop-time-badge">${stop.time_slot || `Option ${idx + 1}`}</span>
          </div>
          
          <div class="stop-card-main-layout">
            <div class="stop-photo-thumb-container" onclick="app.openPhotoLightbox('${safeName}', '${imageUrl}', '${photosUrl}')" title="Click to view full landmark photo">
              <img src="${imageUrl}" alt="${stop.name}" class="stop-thumb-img" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80'">
              <div class="photo-overlay-tag">📸 View Photo</div>
            </div>

            <div class="stop-content">
              <div class="stop-header">
                <div class="stop-title-wrap">
                  <span class="stop-type-icon">${icon}</span>
                  <a href="${photosUrl}" target="_blank" class="stop-title-link" title="Click to view visitor photos & reviews on Google Maps">
                    <h4 class="stop-name">${stop.name} <span class="external-icon">↗</span></h4>
                  </a>
                </div>
                <div class="stop-badge-wrapper">
                  ${this.getCategoryBadge(stop.category || stop.type)}
                </div>
              </div>

              ${stop.description ? `<p class="stop-desc">${stop.description}</p>` : ''}
              ${this.renderWhatToDo(stop.what_to_do)}
              ${stop.signature_dish ? `<p class="stop-specialty"><strong>Signature Dish:</strong> ${stop.signature_dish}</p>` : ''}
              ${stop.notes ? `<p class="stop-notes">💡 <em>${stop.notes}</em></p>` : ''}

              <div class="stop-meta-row">
                ${stop.dwell_time_hours ? `<span class="meta-tag">⏱️ ${stop.dwell_time_hours}h dwell</span>` : ''}
                ${stop.ticket_urgency ? `<span class="meta-tag urgency-pill">${stop.ticket_urgency.toUpperCase()} BOOKING</span>` : ''}
                <span class="meta-tag">⭐ ${stop.rating || 4.8} rating</span>
              </div>

              <div class="stop-actions-row">
                <a href="${photosUrl}" target="_blank" class="btn btn-sm btn-primary">📸 Google Maps & Photos ↗</a>
                <a href="${mapsUrl}" target="_blank" class="btn btn-sm btn-outline">🗺️ Maps Route</a>
                ${stop.ticket_url ? `<a href="${stop.ticket_url}" target="_blank" class="btn btn-sm btn-outline">🎟️ Official Tickets</a>` : ''}
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  toggleStopSelection(dayIndex, stopIndex, isChecked) {
    if (!this.currentTrip || !this.currentTrip.days || !this.currentTrip.days[dayIndex]) return;
    const stop = this.currentTrip.days[dayIndex].stops[stopIndex];
    if (!stop) return;

    stop.selected = isChecked;

    try {
      localStorage.setItem('viaggio_active_trip', JSON.stringify(this.currentTrip));
    } catch (e) {}

    this.renderActiveDayStops();
    this.renderMapForActiveDay();
    this.renderSelectionsView();
  }

  openPhotoLightbox(name, imageUrl, mapsUrl) {
    const modal = document.getElementById('photo-modal');
    const imgEl = document.getElementById('photo-modal-img');
    const titleEl = document.getElementById('photo-modal-title');
    const linkEl = document.getElementById('photo-modal-maps-link');

    if (imgEl) imgEl.src = imageUrl;
    if (titleEl) titleEl.textContent = name;
    if (linkEl) linkEl.href = mapsUrl;

    if (modal) {
      modal.classList.add('open');
      modal.classList.add('active');
    }
  }

  closePhotoLightbox() {
    const modal = document.getElementById('photo-modal');
    if (modal) {
      modal.classList.remove('open');
      modal.classList.remove('active');
    }
  }

  renderSelectionsView() {
    if (!this.currentTrip || !this.currentTrip.days) return;

    const days = this.currentTrip.days;
    let totalSelected = 0;
    let totalActiveHours = 0;
    let totalWalkingKm = 0;
    let diningCount = 0;

    const daysWithSelections = days.map((day, dayIdx) => {
      const selectedStops = (day.stops || []).filter(s => s.selected !== false);
      totalSelected += selectedStops.length;
      
      const dwell = selectedStops.reduce((sum, s) => sum + (s.dwell_time_hours || 1.2), 0);
      const activeH = selectedStops.length > 0 ? dwell + Math.max(0.5, (selectedStops.length - 1) * 0.4) : 0;
      const walkKm = selectedStops.length > 0 ? Math.max(0.5, selectedStops.length * 0.9) : 0;
      
      totalActiveHours += activeH;
      totalWalkingKm += walkKm;
      diningCount += selectedStops.filter(s => s.type === 'lunch' || s.type === 'dinner' || s.type === 'restaurant' || s.category === 'food').length;

      return {
        dayNumber: day.day_number || dayIdx + 1,
        dayIdx: dayIdx,
        theme: day.theme || `Day ${dayIdx + 1}`,
        activeHours: activeH,
        walkingKm: walkKm,
        stops: selectedStops
      };
    });

    // Update badge count in header
    const badgeEl = document.getElementById('selected-stops-badge');
    if (badgeEl) {
      badgeEl.textContent = totalSelected;
    }

    // Render Stats Bar
    const statsBar = document.getElementById('selections-stats-bar');
    if (statsBar) {
      statsBar.innerHTML = `
        <div class="stat-pill"><strong>🎯 ${totalSelected}</strong> Stops Selected</div>
        <div class="stat-pill"><strong>⏱️ ${totalActiveHours.toFixed(1)}h</strong> Total Active Time</div>
        <div class="stat-pill"><strong>🚶 ${totalWalkingKm.toFixed(1)} km</strong> Walking Distance</div>
        <div class="stat-pill"><strong>🍕 ${diningCount}</strong> Authentic Meals & Gelato</div>
      `;
    }

    // Render Selected Days Flow
    const container = document.getElementById('selected-days-container');
    if (!container) return;

    if (totalSelected === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <h3>No stops currently selected in your plan</h3>
          <p>Go to the <strong>📅 Itinerary & Map</strong> tab and check your preferred options for each day to build your custom schedule.</p>
          <button class="btn btn-primary btn-md" onclick="app.switchToTab('tab-itinerary')">📅 Open Daily Options & Select Stops</button>
        </div>
      `;
      return;
    }

    container.innerHTML = daysWithSelections.map(d => {
      return `
        <div class="selection-day-card">
          <div class="selection-day-header">
            <div>
              <h3>📅 Day ${d.dayNumber}: ${d.theme}</h3>
              <span class="selection-day-meta">⏱️ ${d.activeHours.toFixed(1)}h Active · 🚶 ${d.walkingKm.toFixed(1)} km Walking · ${d.stops.length} Selected Stops</span>
            </div>
            <button class="btn btn-outline btn-sm" onclick="app.setActiveDay(${d.dayIdx}); app.switchToTab('tab-itinerary');">✏️ Edit Day ${d.dayNumber} Options</button>
          </div>

          <div class="selection-stops-grid">
            ${d.stops.length === 0 ? '<p class="empty-day-note">No stops selected for this day. Click Edit to add options.</p>' : ''}
            ${d.stops.map((stop, sIdx) => {
              const originalIdx = (this.currentTrip.days[d.dayIdx].stops || []).indexOf(stop);
              const isDining = stop.type === 'lunch' || stop.type === 'dinner' || stop.type === 'restaurant' || stop.category === 'food';
              const icon = isDining ? '🍴' : '🏛️';
              const imageUrl = stop.image_url || stop.imageUrl || 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80';
              let mapsUrl = stop.maps_url || stop.googleMapsUrl || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(stop.name + ', ' + (stop.city || this.currentCity || 'Italy') + ', Italy')}`;
              const photosUrl = stop.google_photos_url || stop.googlePhotosUrl || mapsUrl;
              const safeName = (stop.name || 'Place').replace(/'/g, "\\'");

              return `
                <div class="selected-stop-mini-card">
                  <div class="selected-mini-photo" onclick="app.openPhotoLightbox('${safeName}', '${imageUrl}', '${photosUrl}')">
                    <img src="${imageUrl}" alt="${stop.name}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80'">
                    <span class="mini-photo-badge">📸 View</span>
                  </div>
                  <div class="selected-mini-info">
                    <div class="mini-info-header">
                      <span class="mini-time-tag">${stop.time_slot || `Stop ${sIdx + 1}`}</span>
                      <button class="btn-remove-stop" onclick="app.toggleStopSelection(${d.dayIdx}, ${originalIdx}, false)" title="Remove this stop from custom plan">✕</button>
                    </div>
                    <a href="${photosUrl}" target="_blank" class="mini-stop-title">
                      <strong>${icon} ${stop.name} ↗</strong>
                    </a>
                    <div class="mini-category-tag">
                      ${this.getCategoryBadge(stop.category || stop.type)}
                    </div>
                    <p class="mini-stop-desc">${stop.description || stop.notes || ''}</p>
                    ${this.renderWhatToDo(stop.what_to_do)}
                    ${stop.signature_dish ? `<p class="mini-dish-highlight"><strong>Must Eat:</strong> ${stop.signature_dish}</p>` : ''}
                    <div class="mini-actions">
                      <a href="${photosUrl}" target="_blank" class="mini-link">📸 Photos & Reviews ↗</a>
                      <a href="${mapsUrl}" target="_blank" class="mini-link">🗺️ Maps Route</a>
                      ${stop.ticket_url ? `<a href="${stop.ticket_url}" target="_blank" class="mini-link">🎟️ Tickets</a>` : ''}
                    </div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }).join('');
  }

  // Conversational AI Drawer & Mutations
  async handleSendChat() {
    const input = document.getElementById('chat-input-text');
    if (!input || !input.value.trim()) return;

    const text = input.value.trim();
    input.value = '';
    await this.sendChatMessage(text);
  }

  async sendChatMessage(message) {
    const messagesContainer = document.getElementById('chat-messages-container');
    if (!messagesContainer) return;

    // Append user bubble
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-bubble user';
    userDiv.textContent = message;
    messagesContainer.appendChild(userDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Append thinking bubble
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'chat-bubble assistant thinking';
    const providerLabel = this.selectedLLM === 'groq' ? '⚡ Groq LLM' : (this.selectedLLM === 'gemini' ? '✨ Gemini LLM' : '🔀 Hybrid AI Engine (Groq + Gemini)');
    thinkingDiv.textContent = `🤖 ${providerLabel} analyzing itinerary with Maps MCP...`;
    messagesContainer.appendChild(thinkingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    try {
      const res = await fetch('/api/trips/mutate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trip: this.currentTrip,
          mutation_prompt: message,
          llm_provider: this.selectedLLM || 'auto'
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Mutation failed');
      }

      const data = await res.json();
      this.currentTrip = data.trip;
      try {
        localStorage.setItem('viaggio_active_trip', JSON.stringify(this.currentTrip));
      } catch (e) {
        console.warn('LocalStorage save skipped:', e);
      }
      this.renderItineraryView();
      this.renderSelectionsView();

      thinkingDiv.className = 'chat-bubble assistant';
      thinkingDiv.innerHTML = `
        <strong>✨ Itinerary Updated:</strong><br/>
        ${data.mutation_summary || 'Applied your requested modifications.'}
      `;
    } catch (err) {
      thinkingDiv.className = 'chat-bubble assistant error';
      thinkingDiv.textContent = `Sorry, could not apply changes: ${err.message}`;
    } finally {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  // Live MCP Playground Runner
  async handleRunMcpTool() {
    const tool = document.getElementById('mcp-tool-select').value;
    const argsStr = document.getElementById('mcp-args-json').value;
    const outputEl = document.getElementById('mcp-response-output');
    const runBtn = document.getElementById('mcp-run-tool-btn');

    let parsedArgs = {};
    try {
      parsedArgs = JSON.parse(argsStr);
    } catch (e) {
      alert('Invalid JSON in tool arguments: ' + e.message);
      return;
    }

    if (runBtn) runBtn.disabled = true;
    if (outputEl) outputEl.textContent = `Executing MCP tool "${tool}" via JSON-RPC stdio...`;

    try {
      const res = await fetch('/api/mcp/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool: tool,
          arguments: parsedArgs
        })
      });

      const data = await res.json();
      if (outputEl) {
        outputEl.textContent = JSON.stringify(data, null, 2);
      }
    } catch (err) {
      if (outputEl) {
        outputEl.textContent = 'MCP Call Error: ' + err.message;
      }
    } finally {
      if (runBtn) runBtn.disabled = false;
    }
  }

  // Export & Utilities
  exportTripJSON() {
    if (!this.currentTrip) {
      alert('No active trip to export.');
      return;
    }
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(this.currentTrip, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `viaggio_${this.currentTrip.destination}_${this.currentTrip.duration_days}days.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }

  exportSelectedPlanJSON() {
    if (!this.currentTrip) {
      alert('No active trip to export.');
      return;
    }
    const customTrip = {
      ...this.currentTrip,
      title: `${this.currentTrip.title || this.currentTrip.destination} — My Custom Plan`,
      days: (this.currentTrip.days || []).map(day => ({
        ...day,
        stops: (day.stops || []).filter(s => s.selected !== false)
      }))
    };
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(customTrip, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `viaggio_custom_${this.currentTrip.destination}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }

  copyMarkdownSummary() {
    if (!this.currentTrip) {
      alert('No active trip to copy.');
      return;
    }

    const trip = this.currentTrip;
    let md = `# 🇮🇹 Viaggio Italia — ${trip.title || trip.destination}\n`;
    md += `**Duration:** ${trip.duration_days} Days | **Pace:** ${trip.pace} | **Dietary:** ${trip.dietary_preference}\n\n`;

    (trip.days || []).forEach(day => {
      md += `## Day ${day.day_number}: ${day.theme || ''}\n`;
      md += `- **Pacing:** ${day.pacing_status} (${(day.total_active_hours || 0).toFixed(1)}h active, ${(day.total_walking_km || 0).toFixed(1)}km walking)\n\n`;
      (day.stops || []).forEach(stop => {
        md += `### ${stop.time_slot || 'Stop'}: ${stop.name} (${stop.category || stop.type})\n`;
        if (stop.description) md += `${stop.description}\n`;
        if (stop.signature_dish) md += `- **Signature Dish:** ${stop.signature_dish}\n`;
        if (stop.ticket_url) md += `- **Tickets:** ${stop.ticket_url}\n`;
        if (stop.maps_url) md += `- **Maps:** ${stop.maps_url}\n`;
        md += `\n`;
      });
    });

    navigator.clipboard.writeText(md).then(() => {
      alert('✅ Markdown summary copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy markdown:', err);
    });
  }

  copySelectedPlanMarkdown() {
    if (!this.currentTrip) {
      alert('No active trip to copy.');
      return;
    }
    const trip = this.currentTrip;
    let md = `# 🇮🇹 Viaggio Italia — ${trip.title || trip.destination} (My Selected Plan)\n\n`;

    (trip.days || []).forEach(day => {
      const selected = (day.stops || []).filter(s => s.selected !== false);
      md += `## Day ${day.day_number}: ${day.theme || ''}\n`;
      md += `*${selected.length} Selected Stops*\n\n`;
      selected.forEach(stop => {
        md += `### ${stop.time_slot || 'Stop'}: ${stop.name} (${stop.category || stop.type})\n`;
        if (stop.description) md += `${stop.description}\n`;
        if (stop.signature_dish) md += `- **Signature Dish:** ${stop.signature_dish}\n`;
        if (stop.maps_url) md += `- **Google Maps & Photos:** ${stop.google_photos_url || stop.maps_url}\n`;
        md += `\n`;
      });
    });

    navigator.clipboard.writeText(md).then(() => {
      alert('✅ Custom selected plan copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy markdown:', err);
    });
  }
}

const app = new ViaggioApp();
document.addEventListener('DOMContentLoaded', () => {
  app.init();
});
