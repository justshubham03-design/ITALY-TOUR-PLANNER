import json, pprint

# Destinations
DESTINATIONS = {
    "rome": {
        "id": "rome",
        "name": "Rome",
        "region": "Lazio",
        "center": {"lat": 41.9028, "lng": 12.4964},
        "description": "The Eternal City, rich in ancient history, Vatican treasures, vibrant piazzas, and iconic cuisine.",
        "default_hotel": {"name": "Hotel Artemide (Via Nazionale)", "lat": 41.9015, "lng": 12.4932},
        "airports": ["FCO (Leonardo da Vinci)", "CIA (Ciampino)"],
        "rail_hubs": ["Roma Termini", "Roma Tiburtina"],
        "transit_notes": "Metro lines A & B, extensive tram network, compact walkable historical center. Beware of ZTL in the Centro Storico."
    },
    "sorrento": {
        "id": "sorrento",
        "name": "Sorrento & Amalfi Coast",
        "region": "Campania",
        "center": {"lat": 40.6263, "lng": 14.3758},
        "description": "Cliffside coastal jewel overlooking the Bay of Naples, gateway to Capri, Pompeii, Positano, and Amalfi.",
        "default_hotel": {"name": "Grand Hotel La Favorita (Sorrento)", "lat": 40.6268, "lng": 14.3735},
        "airports": ["NAP (Naples International)"],
        "rail_hubs": ["Sorrento Circumvesuviana Station", "Napoli Centrale"],
        "transit_notes": "Circumvesuviana / Campania Express trains connect Naples to Pompeii & Sorrento. Ferries operate from Marina Piccola to Capri, Positano, and Amalfi. SITA buses serve the Amalfi Drive."
    },
    "bari": {
        "id": "bari",
        "name": "Bari",
        "region": "Puglia",
        "center": {"lat": 41.1171, "lng": 16.8719},
        "description": "Vibrant Adriatic port city famed for Bari Vecchia old town, Basilica di San Nicola, freshly rolled orecchiette, and seaside promenade.",
        "default_hotel": {"name": "Grande Albergo delle Nazioni (Lungomare)", "lat": 41.1215, "lng": 16.8765},
        "airports": ["BRI (Bari Karol Wojtyla Airport)"],
        "rail_hubs": ["Bari Centrale"],
        "transit_notes": "Bari Vecchia is strictly pedestrian. Ferrovie del Sud Est (FSE) and Trenitalia connect Bari to Polignano a Mare, Monopoli, and Alberobello."
    },
    "puglia": {
        "id": "puglia",
        "name": "Puglia & Valle d'Itria",
        "region": "Puglia",
        "center": {"lat": 40.7850, "lng": 17.2400},
        "description": "Enchanting southern region known for whitewashed Trulli of Alberobello, cliffside Polignano a Mare, Baroque Lecce, and ancient olive groves.",
        "default_hotel": {"name": "Masseria Torre Coccaro (Fasano / Savelletri)", "lat": 40.8654, "lng": 17.3821},
        "airports": ["BRI (Bari)", "BDS (Brindisi)"],
        "rail_hubs": ["Bari Centrale", "Brindisi", "Lecce"],
        "transit_notes": "Renting a car is highly recommended for exploring Valle d'Itria towns (Locorotondo, Martina Franca, Ostuni) and secluded coastal coves."
    },
    "milan": {
        "id": "milan",
        "name": "Milan",
        "region": "Lombardy",
        "center": {"lat": 45.4642, "lng": 9.1900},
        "description": "Italy's fashion and design capital, home to the Duomo, Da Vinci's Last Supper, historic canals of Navigli, and world-class opera at La Scala.",
        "default_hotel": {"name": "Rosa Grand Milano (Duomo)", "lat": 45.4636, "lng": 9.1938},
        "airports": ["MXP (Malpensa)", "LIN (Linate)", "BGY (Orio al Serio)"],
        "rail_hubs": ["Milano Centrale", "Milano Cadorna", "Milano Garibaldi"],
        "transit_notes": "Exceptional Metro system (M1, M2, M3, M4, M5), historic yellow trams, Area C congestion charge for cars."
    },
    "lake_garda": {
        "id": "lake_garda",
        "name": "Lake Garda",
        "region": "Veneto / Lombardy / Trentino",
        "center": {"lat": 45.5600, "lng": 10.6300},
        "description": "Italy's largest lake, featuring dramatic northern alpine fjords, thermal southern peninsulas (Sirmione), Scaliger castles, and lemon groves.",
        "default_hotel": {"name": "Villa Cortine Palace Hotel (Sirmione)", "lat": 45.4988, "lng": 10.6062},
        "airports": ["VRN (Verona Catullo)", "BGY (Milan Bergamo)", "MXP (Milan Malpensa)"],
        "rail_hubs": ["Desenzano del Garda", "Peschiera del Garda"],
        "transit_notes": "Navigazione Laghi passenger ferries and hydrofoils provide scenic lake transport between Sirmione, Malcesine, Riva del Garda, and Limone sul Garda."
    }
}

PLACES = [
    {
        "place_id": "it_rom_colosseum",
        "name": "Colosseum & Roman Forum",
        "city_id": "rome",
        "city": "Rome",
        "category": "historical",
        "types": ["tourist_attraction", "historical_landmark", "museum"],
        "coordinates": {"lat": 41.8902, "lng": 12.4922},
        "address": "Piazza del Colosseo, 1, 00184 Roma RM, Italy",
        "rating": 4.8,
        "user_ratings_total": 350000,
        "price_level": "€€",
        "typical_dwell_minutes": 150,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Monday-Sunday: 8:30 AM – 7:15 PM"]
        },
        "booking_urgency": "urgent",
        "booking_lead_time": "30 days prior (released at 08:45 Rome time)",
        "official_booking_url": "https://ticketing.colosseo.it/en/",
        "best_time_of_day": "morning",
        "description": "Iconic ancient amphitheater commissioned in AD 72 and the neighboring Roman Forum, the civic center of the ancient Roman Empire.",
        "local_tips": "Book the Full Experience Arena/Underground ticket 30 days ahead exactly when slots open. Entry line can exceed 2 hours without reserved timed entry."
    },
    {
        "place_id": "it_rom_vatican",
        "name": "Vatican Museums & Sistine Chapel",
        "city_id": "rome",
        "city": "Rome",
        "category": "museums",
        "types": ["museum", "tourist_attraction", "church"],
        "coordinates": {"lat": 41.9067, "lng": 12.4536},
        "address": "00120 Vatican City",
        "rating": 4.7,
        "user_ratings_total": 175000,
        "price_level": "€€",
        "typical_dwell_minutes": 180,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Monday-Saturday: 8:00 AM – 7:00 PM", "Sunday: Closed"]
        },
        "booking_urgency": "urgent",
        "booking_lead_time": "60 days prior",
        "official_booking_url": "https://tickets.museivaticani.va/",
        "best_time_of_day": "morning",
        "description": "Vast complex of papal art galleries featuring Michelangelo's Sistine Chapel ceiling and Raphael's Rooms.",
        "local_tips": "Strict dress code: shoulders and knees must be covered. Closed on most Sundays. Reserve prime morning slots (8:30 AM) to avoid midday peak crowding."
    },
    {
        "place_id": "it_rom_st_peters",
        "name": "St. Peter's Basilica & Dome Climb",
        "city_id": "rome",
        "city": "Rome",
        "category": "churches",
        "types": ["church", "tourist_attraction", "historical_landmark"],
        "coordinates": {"lat": 41.9022, "lng": 12.4539},
        "address": "Piazza San Pietro, 00120 Citta del Vaticano",
        "rating": 4.8,
        "user_ratings_total": 140000,
        "price_level": "Free (Dome climb €10)",
        "typical_dwell_minutes": 100,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Daily: 7:00 AM – 7:00 PM (Wed opens 12:30 PM)"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "Basilica free; dome climb ticket on-site",
        "official_booking_url": "https://www.basilicasanpietro.va/en/",
        "best_time_of_day": "early_morning",
        "description": "The epicenter of Catholicism and renaissance architecture designed by Michelangelo, Bernini, and Bramante.",
        "local_tips": "Arrive by 7:15 AM to enter security line without waiting. Climb the 551 steps of the Cupola for 360° panoramic view of Rome."
    },
    {
        "place_id": "it_rom_pantheon",
        "name": "Pantheon",
        "city_id": "rome",
        "city": "Rome",
        "category": "historical",
        "types": ["historical_landmark", "tourist_attraction", "church"],
        "coordinates": {"lat": 41.8986, "lng": 12.4769},
        "address": "Piazza della Rotonda, 00186 Roma RM, Italy",
        "rating": 4.8,
        "user_ratings_total": 210000,
        "price_level": "€",
        "typical_dwell_minutes": 45,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Daily: 9:00 AM – 7:00 PM"]
        },
        "booking_urgency": "advance",
        "booking_lead_time": "1-7 days prior (required on weekends)",
        "official_booking_url": "https://www.museiitaliani.it/",
        "best_time_of_day": "midday",
        "description": "Ancient Roman temple dedicated to all gods, featuring the world's largest unreinforced concrete dome and open oculus.",
        "local_tips": "Since July 2023, a €5 ticket is mandatory. Weekend entry requires advance booking online."
    },
    {
        "place_id": "it_rom_trevi",
        "name": "Trevi Fountain (Fontana di Trevi)",
        "city_id": "rome",
        "city": "Rome",
        "category": "viewpoints",
        "types": ["tourist_attraction", "historical_landmark"],
        "coordinates": {"lat": 41.9009, "lng": 12.4833},
        "address": "Piazza di Trevi, 00187 Roma RM, Italy",
        "rating": 4.8,
        "user_ratings_total": 390000,
        "price_level": "Free",
        "typical_dwell_minutes": 30,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open 24 hours daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "early_morning_or_late_evening",
        "description": "Baroque masterpiece designed by Nicola Salvi, featuring Oceanus flanked by tritons and mythological horses.",
        "local_tips": "Visit at 7:00 AM for serenity or after 10:30 PM under golden illumination. Toss coin with right hand over left shoulder."
    },
    {
        "place_id": "it_rom_borghese",
        "name": "Borghese Gallery and Museum",
        "city_id": "rome",
        "city": "Rome",
        "category": "museums",
        "types": ["museum", "art_gallery", "tourist_attraction"],
        "coordinates": {"lat": 41.9142, "lng": 12.4922},
        "address": "Piazzale Scipione Borghese, 5, 00197 Roma RM, Italy",
        "rating": 4.7,
        "user_ratings_total": 35000,
        "price_level": "€€",
        "typical_dwell_minutes": 120,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Tuesday to Sunday: 9:00 AM – 7:00 PM", "Monday: Closed"]
        },
        "booking_urgency": "urgent",
        "booking_lead_time": "14-30 days prior (Mandatory reserved 2-hour entry slot)",
        "official_booking_url": "https://www.galleriaborghese.it/",
        "best_time_of_day": "morning",
        "description": "Stunning villa housing cardinal Scipione Borghese's private collection of Bernini sculptures and Caravaggio masterpieces.",
        "local_tips": "Strict 2-hour time limit per session. Book well in advance as daily capacity is capped at 360 visitors per slot."
    },
    {
        "place_id": "it_rom_trastevere",
        "name": "Trastevere Historic Quarter & Piazza Santa Maria",
        "city_id": "rome",
        "city": "Rome",
        "category": "viewpoints",
        "types": ["tourist_attraction", "neighborhood", "point_of_interest"],
        "coordinates": {"lat": 41.8895, "lng": 12.4705},
        "address": "Piazza di Santa Maria in Trastevere, 00153 Roma RM, Italy",
        "rating": 4.7,
        "user_ratings_total": 45000,
        "price_level": "Free",
        "typical_dwell_minutes": 90,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open 24 hours daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "evening",
        "description": "Charming bohemian quarter with cobblestone alleys, ivy-draped facades, vibrant street musicians, and artisan osterias.",
        "local_tips": "Ideal for sunset aperitivo and late-night Roman dinner. Stroll up to Gianicolo Hill for panoramic sunset view over Rome."
    },

    # SORRENTO
    {
        "place_id": "it_sor_historic_centre",
        "name": "Sorrento Centro Storico & Sedil Dominova",
        "city_id": "sorrento",
        "city": "Sorrento",
        "category": "historical",
        "types": ["neighborhood", "tourist_attraction", "shopping_mall"],
        "coordinates": {"lat": 40.6263, "lng": 14.3758},
        "address": "Via San Cesareo, 80067 Sorrento NA, Italy",
        "rating": 4.7,
        "user_ratings_total": 28000,
        "price_level": "Free",
        "typical_dwell_minutes": 90,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open daily 9:00 AM – 11:30 PM"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "afternoon_evening",
        "description": "Vibrant pedestrian heart of Sorrento, famous for artisan wood intarsio workshops, limoncello distilleries, and 14th-century Sedil Dominova.",
        "local_tips": "Stroll down Via San Cesareo for authentic handmade lemon artisanal products and free limoncello tastings."
    },
    {
        "place_id": "it_sor_marina_grande",
        "name": "Marina Grande Fisherman's Village",
        "city_id": "sorrento",
        "city": "Sorrento",
        "category": "beaches",
        "types": ["tourist_attraction", "harbor", "beach"],
        "coordinates": {"lat": 40.6288, "lng": 14.3685},
        "address": "Via Marina Grande, 80067 Sorrento NA, Italy",
        "rating": 4.7,
        "user_ratings_total": 32000,
        "price_level": "Free",
        "typical_dwell_minutes": 75,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open 24 hours daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "lunch_or_sunset",
        "description": "Picturesque pastel-colored fishing village tucked below Sorrento's cliffs with historic wooden gozzi boats and waterside trattorias.",
        "local_tips": "Walk down via the ancient Greek gate (Porta Marina Grande). Perfect spot for sunset dining by the water."
    },
    {
        "place_id": "it_sor_bagni_regina",
        "name": "Bagni della Regina Giovanna (Queen Joan's Baths)",
        "city_id": "sorrento",
        "city": "Sorrento",
        "category": "beaches",
        "types": ["natural_feature", "tourist_attraction", "historical_landmark"],
        "coordinates": {"lat": 40.6306, "lng": 14.3533},
        "address": "Traversa Punta Capo, 80067 Sorrento NA, Italy",
        "rating": 4.6,
        "user_ratings_total": 16500,
        "price_level": "Free",
        "typical_dwell_minutes": 120,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open daily sunrise to sunset"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "morning_or_afternoon",
        "description": "Secluded emerald sea lagoon enclosed by limestone cliffs and the ruins of the 1st-century BC Roman Villa of Pollio Felice.",
        "local_tips": "Take bus line A from Piazza Tasso to Capo di Sorrento, then walk 15 mins down cobblestone trail. Wear sturdy water shoes."
    },
    {
        "place_id": "it_sor_pompeii",
        "name": "Pompeii Archaeological Park",
        "city_id": "sorrento",
        "city": "Pompeii / Campania",
        "category": "historical",
        "types": ["historical_landmark", "museum", "tourist_attraction"],
        "coordinates": {"lat": 40.7490, "lng": 14.4848},
        "address": "Via Plinio, 26, 80045 Pompei NA, Italy",
        "rating": 4.8,
        "user_ratings_total": 125000,
        "price_level": "€€",
        "typical_dwell_minutes": 210,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Daily: 9:00 AM – 7:00 PM (Apr-Oct); 9:00 AM – 5:00 PM (Nov-Mar)"]
        },
        "booking_urgency": "urgent",
        "booking_lead_time": "7-14 days prior (Fast-track entry)",
        "official_booking_url": "https://www.pompeisites.org/",
        "best_time_of_day": "morning",
        "description": "World-famous ancient Roman city preserved under meters of volcanic ash following the eruption of Mount Vesuvius in AD 79.",
        "local_tips": "Take the Circumvesuviana train from Sorrento station (20 mins to Pompei Scavi). Bring sun hat, water bottle, and book timed entry."
    },
    {
        "place_id": "it_sor_capri_ferry",
        "name": "Isle of Capri Day Excursion & Faraglioni",
        "city_id": "sorrento",
        "city": "Capri / Sorrento",
        "category": "viewpoints",
        "types": ["tourist_attraction", "natural_feature", "island"],
        "coordinates": {"lat": 40.5507, "lng": 14.2426},
        "address": "Marina Grande, 80073 Capri NA, Italy",
        "rating": 4.7,
        "user_ratings_total": 48000,
        "price_level": "€€€",
        "typical_dwell_minutes": 360,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Ferries operate 7:00 AM – 7:30 PM daily (High season)"]
        },
        "booking_urgency": "urgent",
        "booking_lead_time": "7-21 days prior for high-speed hydrofoil",
        "official_booking_url": "https://www.caremar.it/",
        "best_time_of_day": "full_day",
        "description": "Legendary Mediterranean island featuring the Faraglioni rock formations, Gardens of Augustus, and Anacapri chairlift to Monte Solaro.",
        "local_tips": "Catch 8:30 AM fast hydrofoil from Sorrento Marina Piccola (25 min ride). Blue Grotto rowing boats depend strictly on calm sea swells."
    },
    {
        "place_id": "it_sor_villa_comunale",
        "name": "Villa Comunale Park & Sunset Terrace",
        "city_id": "sorrento",
        "city": "Sorrento",
        "category": "viewpoints",
        "types": ["park", "tourist_attraction", "scenic_viewpoint"],
        "coordinates": {"lat": 40.6275, "lng": 14.3739},
        "address": "Via San Francesco, 80067 Sorrento NA, Italy",
        "rating": 4.8,
        "user_ratings_total": 19000,
        "price_level": "Free",
        "typical_dwell_minutes": 40,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open daily 8:00 AM – 11:00 PM"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "sunset",
        "description": "Public park perched on Sorrento's cliff edge with sweeping panoramic views of the Gulf of Naples and Mount Vesuvius.",
        "local_tips": "Take the Sorrento Lift (€1.10) directly from Villa Comunale down to Marina Piccola ferry pier."
    },

    # BARI
    {
        "place_id": "it_bar_bari_vecchia",
        "name": "Bari Vecchia & Orecchiette Street",
        "city_id": "bari",
        "city": "Bari",
        "category": "historical",
        "types": ["neighborhood", "tourist_attraction", "point_of_interest"],
        "coordinates": {"lat": 41.1292, "lng": 16.8700},
        "address": "Strada Arco Basso, 70122 Bari BA, Italy",
        "rating": 4.8,
        "user_ratings_total": 24000,
        "price_level": "Free",
        "typical_dwell_minutes": 90,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Best visited 9:30 AM – 1:00 PM and 4:30 PM – 7:30 PM"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "morning",
        "description": "Medieval walled quarter where local nonnas sit outside their front doors swiftly hand-rolling fresh orecchiette pasta.",
        "local_tips": "Buy a bag of sun-dried orecchiette directly from Signora Nunzia on Arco Basso (€3-€5). Pair with turnip greens (cime di rapa)."
    },
    {
        "place_id": "it_bar_san_nicola",
        "name": "Basilica di San Nicola",
        "city_id": "bari",
        "city": "Bari",
        "category": "churches",
        "types": ["church", "historical_landmark", "tourist_attraction"],
        "coordinates": {"lat": 41.1303, "lng": 16.8708},
        "address": "Largo Abate Elia, 13, 70122 Bari BA, Italy",
        "rating": 4.8,
        "user_ratings_total": 22000,
        "price_level": "Free",
        "typical_dwell_minutes": 60,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Monday-Saturday: 7:00 AM – 8:30 PM", "Sunday: 7:00 AM – 10:00 PM"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "https://www.basilicasannicola.it/",
        "best_time_of_day": "morning_or_afternoon",
        "description": "11th-century Romanesque masterpiece housing the sacred relics of Saint Nicholas.",
        "local_tips": "Descend into the Romanesque crypt with 28 columns to see the tomb of Saint Nicholas."
    },
    {
        "place_id": "it_bar_lungomare",
        "name": "Lungomare Nazario Sauro & Harbor",
        "city_id": "bari",
        "city": "Bari",
        "category": "viewpoints",
        "types": ["tourist_attraction", "park", "seafood_market"],
        "coordinates": {"lat": 41.1245, "lng": 16.8770},
        "address": "Lungomare Nazario Sauro, 70121 Bari BA, Italy",
        "rating": 4.7,
        "user_ratings_total": 18000,
        "price_level": "Free",
        "typical_dwell_minutes": 60,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Morning fish market 8:00 AM – 1:00 PM; promenade open 24h"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "morning_or_sunset",
        "description": "Italy's longest seaside promenade lined with grand architecture, featuring the traditional raw seafood morning market.",
        "local_tips": "At Molo San Nicola in the morning, watch fishermen curl fresh octopus and enjoy a cold Peroni beer."
    },
    {
        "place_id": "it_bar_castello_svevo",
        "name": "Castello Normanno-Svevo",
        "city_id": "bari",
        "city": "Bari",
        "category": "historical",
        "types": ["castle", "museum", "historical_landmark"],
        "coordinates": {"lat": 41.1287, "lng": 16.8647},
        "address": "Piazza Federico II di Svevia, 4, 70122 Bari BA, Italy",
        "rating": 4.5,
        "user_ratings_total": 9500,
        "price_level": "€",
        "typical_dwell_minutes": 75,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Wednesday-Monday: 9:00 AM – 7:00 PM", "Tuesday: Closed"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "Tickets at entrance (€6)",
        "official_booking_url": "https://musei.puglia.beniculturali.it/musei/castello-svevo-di-bari/",
        "best_time_of_day": "morning",
        "description": "Imposing 12th-century Norman fortress rebuilt by Holy Roman Emperor Frederick II, surrounded by a deep moat.",
        "local_tips": "Includes an impressive plaster cast gallery of Romanesque architectural details from across Puglia."
    },

    # PUGLIA
    {
        "place_id": "it_pug_alberobello",
        "name": "Rione Monti Trulli of Alberobello (UNESCO)",
        "city_id": "puglia",
        "city": "Alberobello",
        "category": "historical",
        "types": ["tourist_attraction", "historical_landmark", "neighborhood"],
        "coordinates": {"lat": 40.7838, "lng": 17.2369},
        "address": "Rione Monti, 70011 Alberobello BA, Italy",
        "rating": 4.8,
        "user_ratings_total": 42000,
        "price_level": "Free",
        "typical_dwell_minutes": 150,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open 24 hours daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "early_morning_or_late_afternoon",
        "description": "Fairytale town of over 1,500 drystone conical limestone huts built without mortar dating back to the 14th century.",
        "local_tips": "Head to Belvedere Santa Lucia for iconic postcard views. Explore Rione Aia Piccola for residential trulli."
    },
    {
        "place_id": "it_pug_polignano",
        "name": "Polignano a Mare & Lama Monachile Beach",
        "city_id": "puglia",
        "city": "Polignano a Mare",
        "category": "beaches",
        "types": ["tourist_attraction", "beach", "scenic_viewpoint"],
        "coordinates": {"lat": 40.9961, "lng": 17.2195},
        "address": "Lama Monachile, 70044 Polignano a Mare BA, Italy",
        "rating": 4.8,
        "user_ratings_total": 38000,
        "price_level": "Free",
        "typical_dwell_minutes": 120,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open 24 hours daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "afternoon_sunset",
        "description": "Dramatically perched on limestone cliffs above turquoise Adriatic water, famous for the Roman bridge and cliff diving.",
        "local_tips": "Order a famous 'Caffe Speciale' (espresso with lemon peel, amaretto, and whipped cream) at Il Supermago del Gelo."
    },
    {
        "place_id": "it_pug_ostuni",
        "name": "Ostuni Centro Storico (The White City)",
        "city_id": "puglia",
        "city": "Ostuni",
        "category": "historical",
        "types": ["neighborhood", "historical_landmark", "tourist_attraction"],
        "coordinates": {"lat": 40.7282, "lng": 17.5786},
        "address": "Piazza della Liberta, 72017 Ostuni BR, Italy",
        "rating": 4.7,
        "user_ratings_total": 29000,
        "price_level": "Free",
        "typical_dwell_minutes": 120,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open 24 hours daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "late_afternoon_sunset",
        "description": "Labyrinthine whitewashed hilltop citadel overlooking an endless plain of olive trees stretching to the Adriatic.",
        "local_tips": "Wander the winding stone staircases to the 15th-century Cathedral and find the famous green door view (Porta Blu)."
    },
    {
        "place_id": "it_pug_matera",
        "name": "Sassi di Matera Cave Dwellings (UNESCO)",
        "city_id": "puglia",
        "city": "Matera",
        "category": "historical",
        "types": ["historical_landmark", "tourist_attraction", "neighborhood"],
        "coordinates": {"lat": 40.6664, "lng": 16.6087},
        "address": "Piazza San Pietro Caveoso, 75100 Matera MT, Italy",
        "rating": 4.9,
        "user_ratings_total": 52000,
        "price_level": "Free",
        "typical_dwell_minutes": 240,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open 24 hours daily"]
        },
        "booking_urgency": "advance",
        "booking_lead_time": "1-3 days prior for rupestrian church pass",
        "official_booking_url": "https://www.materaturismo.it/",
        "best_time_of_day": "afternoon_evening",
        "description": "One of the oldest continuously inhabited cities in human history, carved directly into dramatic limestone canyon rock.",
        "local_tips": "Wear sturdy walking shoes with grip. The lighting at dusk makes the ancient cave ravines resemble a living Nativity scene."
    },

    # MILAN
    {
        "place_id": "it_mil_duomo",
        "name": "Duomo di Milano & Rooftop Terraces",
        "city_id": "milan",
        "city": "Milan",
        "category": "historical",
        "types": ["church", "historical_landmark", "tourist_attraction"],
        "coordinates": {"lat": 45.4641, "lng": 9.1919},
        "address": "Piazza del Duomo, 20122 Milano MI, Italy",
        "rating": 4.8,
        "user_ratings_total": 160000,
        "price_level": "€€",
        "typical_dwell_minutes": 120,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Daily: 9:00 AM – 7:00 PM (Last entry 6:10 PM)"]
        },
        "booking_urgency": "urgent",
        "booking_lead_time": "7-14 days prior (Mandatory timed ticket)",
        "official_booking_url": "https://ticket.duomomilano.it/",
        "best_time_of_day": "morning_or_late_afternoon",
        "description": "Spectacular Italian Gothic cathedral adorned with 3,400 statues, 135 gargoyles, and pink Candoglia marble.",
        "local_tips": "Purchase the 'Duomo Pass with Rooftop by Lift' to walk among marble spires with views extending to the Italian Alps."
    },
    {
        "place_id": "it_mil_last_supper",
        "name": "Leonardo da Vinci's Last Supper (Cenacolo Vinciano)",
        "city_id": "milan",
        "city": "Milan",
        "category": "museums",
        "types": ["museum", "historical_landmark", "art_gallery"],
        "coordinates": {"lat": 45.4660, "lng": 9.1710},
        "address": "Piazza di Santa Maria delle Grazie, 2, 20123 Milano MI, Italy",
        "rating": 4.8,
        "user_ratings_total": 45000,
        "price_level": "€€",
        "typical_dwell_minutes": 45,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Tuesday to Sunday: 8:15 AM – 7:00 PM", "Monday: Closed"]
        },
        "booking_urgency": "urgent",
        "booking_lead_time": "60-90 days prior (Strict booking quotas)",
        "official_booking_url": "https://cenacolovinciano.vivaticket.it/",
        "best_time_of_day": "morning",
        "description": "Leonardo da Vinci's monumental 15th-century masterpiece painted on the refectory wall of Santa Maria delle Grazie.",
        "local_tips": "Tickets drop every 3 months and sell out in minutes. Arrive 30 minutes prior to exchange voucher for official pass."
    },
    {
        "place_id": "it_mil_galleria",
        "name": "Galleria Vittorio Emanuele II",
        "city_id": "milan",
        "city": "Milan",
        "category": "shopping",
        "types": ["shopping_mall", "historical_landmark", "tourist_attraction"],
        "coordinates": {"lat": 45.4657, "lng": 9.1900},
        "address": "Piazza del Duomo, 20123 Milano MI, Italy",
        "rating": 4.7,
        "user_ratings_total": 98000,
        "price_level": "Free (Luxury shopping)",
        "typical_dwell_minutes": 60,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open 24 hours daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "afternoon_evening",
        "description": "Grand 19th-century glass-vaulted arcade housing luxury fashion flagships and historic cafes.",
        "local_tips": "Spin three times with right heel on the bull's testicles mosaic floor for good luck."
    },
    {
        "place_id": "it_mil_castello",
        "name": "Castello Sforzesco & Parco Sempione",
        "city_id": "milan",
        "city": "Milan",
        "category": "historical",
        "types": ["castle", "park", "museum"],
        "coordinates": {"lat": 45.4705, "lng": 9.1794},
        "address": "Piazza Castello, 20121 Milano MI, Italy",
        "rating": 4.6,
        "user_ratings_total": 78000,
        "price_level": "Courtyards Free (Museums €5)",
        "typical_dwell_minutes": 90,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Courtyards: 7:00 AM – 7:30 PM daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "On-site",
        "official_booking_url": "https://www.milanocastello.it/",
        "best_time_of_day": "morning_or_afternoon",
        "description": "Massive 15th-century red-brick Renaissance citadel built by Francesco Sforza, Duke of Milan.",
        "local_tips": "Walk through the castle courtyards directly into Parco Sempione and stroll to the Arco della Pace."
    },
    {
        "place_id": "it_mil_navigli",
        "name": "Navigli Canals & Darsena Basin",
        "city_id": "milan",
        "city": "Milan",
        "category": "viewpoints",
        "types": ["neighborhood", "tourist_attraction", "nightlife"],
        "coordinates": {"lat": 45.4514, "lng": 9.1764},
        "address": "Alzaia Naviglio Grande, 20144 Milano MI, Italy",
        "rating": 4.6,
        "user_ratings_total": 45000,
        "price_level": "€€",
        "typical_dwell_minutes": 120,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Aperitivo and dining vibrant from 6:00 PM to 1:00 AM daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "Table reservations recommended on weekends",
        "official_booking_url": "",
        "best_time_of_day": "evening",
        "description": "Historic canal district designed in part by Leonardo da Vinci, now the epicenter of Milanese aperitivo culture.",
        "local_tips": "Arrive at 6:30 PM along Naviglio Grande for classic Milanese aperitivo buffet (Campari Spritz + appetizers)."
    },

    # LAKE GARDA
    {
        "place_id": "it_gar_sirmione_castle",
        "name": "Castello Scaligero of Sirmione",
        "city_id": "lake_garda",
        "city": "Sirmione",
        "category": "historical",
        "types": ["castle", "tourist_attraction", "historical_landmark"],
        "coordinates": {"lat": 45.4930, "lng": 10.6080},
        "address": "Piazza Castello, 34, 25019 Sirmione BS, Italy",
        "rating": 4.7,
        "user_ratings_total": 36000,
        "price_level": "€",
        "typical_dwell_minutes": 75,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Tuesday to Sunday: 8:30 AM – 7:15 PM", "Monday: Closed"]
        },
        "booking_urgency": "advance",
        "booking_lead_time": "3-7 days prior in summer",
        "official_booking_url": "https://musei.lombardia.beniculturali.it/musei/castello-scaligero-di-sirmione/",
        "best_time_of_day": "morning",
        "description": "Spectacular 14th-century water fortress completely surrounded by Lake Garda with a rare preserved fortified harbor.",
        "local_tips": "Climb the 146 steps of the main keep for unforgettable panoramic views of Sirmione peninsula."
    },
    {
        "place_id": "it_gar_grotte_catullo",
        "name": "Grotte di Catullo Roman Villa & Jamaica Beach",
        "city_id": "lake_garda",
        "city": "Sirmione",
        "category": "beaches",
        "types": ["historical_landmark", "museum", "beach"],
        "coordinates": {"lat": 45.5008, "lng": 10.6056},
        "address": "Piazzale Orti Manara, 4, 25019 Sirmione BS, Italy",
        "rating": 4.7,
        "user_ratings_total": 24000,
        "price_level": "€",
        "typical_dwell_minutes": 120,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Tuesday to Saturday: 8:30 AM – 7:30 PM", "Monday: Closed"]
        },
        "booking_urgency": "advance",
        "booking_lead_time": "1-3 days prior in peak season",
        "official_booking_url": "https://musei.lombardia.beniculturali.it/musei/grotte-di-catullo/",
        "best_time_of_day": "morning_or_afternoon",
        "description": "Ruins of the grandest Roman villa in Northern Italy, perched on olive-clad cliffs at the tip of the peninsula.",
        "local_tips": "Walk down to Jamaica Beach below the ruins for swimming on flat limestone rock shelves in crystal-clear water."
    },
    {
        "place_id": "it_gar_malcesine_cablecar",
        "name": "Malcesine Scaliger Castle & Monte Baldo Rotating Cableway",
        "city_id": "lake_garda",
        "city": "Malcesine",
        "category": "viewpoints",
        "types": ["tourist_attraction", "castle", "natural_feature"],
        "coordinates": {"lat": 45.7645, "lng": 10.8080},
        "address": "Via Navene Vecchia, 12, 37018 Malcesine VR, Italy",
        "rating": 4.8,
        "user_ratings_total": 27000,
        "price_level": "€€€",
        "typical_dwell_minutes": 180,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Cable car runs daily 8:00 AM – 6:00 PM every 30 minutes"]
        },
        "booking_urgency": "urgent",
        "booking_lead_time": "3-7 days prior for fast-track cable car ticket",
        "official_booking_url": "https://funiviamalcesine.com/",
        "best_time_of_day": "morning",
        "description": "World-famous rotating cable car ascending from lakeside medieval Malcesine to the alpine heights of Monte Baldo (1,760m).",
        "local_tips": "The second section of the cable car cabin rotates 360° during the ascent. Bring a fleece jacket even in midsummer."
    },
    {
        "place_id": "it_gar_limone",
        "name": "Limone sul Garda & Ciclovia del Garda Suspended Skywalk",
        "city_id": "lake_garda",
        "city": "Limone sul Garda",
        "category": "viewpoints",
        "types": ["tourist_attraction", "hiking_area", "point_of_interest"],
        "coordinates": {"lat": 45.8150, "lng": 10.7930},
        "address": "Via Lungolago Marconi, 25010 Limone Sul Garda BS, Italy",
        "rating": 4.8,
        "user_ratings_total": 21000,
        "price_level": "Free",
        "typical_dwell_minutes": 120,
        "opening_hours": {
            "open_now": True,
            "weekday_descriptions": ["Open 24 hours daily"]
        },
        "booking_urgency": "optional",
        "booking_lead_time": "None",
        "official_booking_url": "",
        "best_time_of_day": "morning_or_afternoon",
        "description": "Charming village tucked beneath sheer rock faces, famous for historical terraced lemon houses and suspended skywalk.",
        "local_tips": "Take the passenger ferry from Malcesine directly across to Limone (20 mins)."
    }
]

RESTAURANTS = [
    # ROME
    {
        "place_id": "it_res_rom_da_enzo",
        "name": "Trattoria Da Enzo al 29",
        "city_id": "rome",
        "city": "Rome",
        "neighborhood": "Trastevere",
        "coordinates": {"lat": 41.8872, "lng": 12.4784},
        "address": "Via dei Vascellari, 29, 00153 Roma RM, Italy",
        "rating": 4.7,
        "user_ratings_total": 6500,
        "price_level": "€€",
        "cuisine_types": ["Roman", "Trattoria", "Pasta"],
        "dietary_tier": "vegetarian_friendly",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Cacio e Pepe [VEG]",
            "Carciofo alla Giudia [VEG]",
            "Rigatoni alla Carbonara",
            "Tiramisu al Mascarpone [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Walk-in queue or call 2 weeks prior",
        "opening_hours": "Mon-Sat: 12:15 PM – 3:00 PM, 7:15 PM – 11:00 PM",
        "local_notes": "Legendary authentic Roman trattoria. Line forms 30 mins before dinner opening."
    },
    {
        "place_id": "it_res_rom_roscioli",
        "name": "Roscioli Salumeria con Cucina",
        "city_id": "rome",
        "city": "Rome",
        "neighborhood": "Campo de' Fiori",
        "coordinates": {"lat": 41.8943, "lng": 12.4740},
        "address": "Via dei Giubbonari, 21, 00186 Roma RM, Italy",
        "rating": 4.6,
        "user_ratings_total": 8200,
        "price_level": "€€€",
        "cuisine_types": ["Roman", "Salumeria", "Fine Casual"],
        "dietary_tier": "vegetarian_friendly",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Spaghettoni Cacio e Pepe [VEG]",
            "Burrata Pugliese con Pomodorini Semi-Secchi [VEG]",
            "Carbonara con Guanciale Artigianale"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 3-4 weeks in advance online",
        "opening_hours": "Daily: 12:30 PM – 4:00 PM, 7:00 PM – 11:30 PM",
        "local_notes": "A culinary institution inside a historic gourmet deli."
    },
    {
        "place_id": "it_res_rom_ba_ghetto",
        "name": "Ba'Ghetto Milky (Kosher / Jewish-Roman)",
        "city_id": "rome",
        "city": "Rome",
        "neighborhood": "Jewish Ghetto",
        "coordinates": {"lat": 41.8926, "lng": 12.4777},
        "address": "Via del Portico d'Ottavia, 2A, 00186 Roma RM, Italy",
        "rating": 4.5,
        "user_ratings_total": 3400,
        "price_level": "€€",
        "cuisine_types": ["Jewish-Roman", "Vegetarian", "Dairy Kosher"],
        "dietary_tier": "naturally_vegetarian",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Authentic Carciofo alla Giudia [VEG]",
            "Fiori di Zucca Fritti con Mozzarella [VEG]",
            "Torta di Ricotta e Visciole [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 3-7 days ahead",
        "opening_hours": "Sun-Thu: 12:00 PM – 11:00 PM; Fri: 12:00 PM – 3:30 PM",
        "local_notes": "The Roman Jewish quarter's benchmark for dairy and vegetarian cuisine."
    },
    {
        "place_id": "it_res_rom_bonci",
        "name": "Pizzarium Bonci",
        "city_id": "rome",
        "city": "Rome",
        "neighborhood": "Vatican / Prati",
        "coordinates": {"lat": 41.9073, "lng": 12.4475},
        "address": "Via della Meloria, 43, 00136 Roma RM, Italy",
        "rating": 4.6,
        "user_ratings_total": 12000,
        "price_level": "€€",
        "cuisine_types": ["Pizza al Taglio", "Street Food", "Bakery"],
        "dietary_tier": "naturally_vegetarian",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Pizza al Taglio con Patate e Rosmarino [VEG]",
            "Pizza Margherita con Pomodoro del Piennolo [VEG]",
            "Suppli al Telefono Tradizionale [VEG]"
        ],
        "reservation_recommended": False,
        "reservation_urgency": "Take ticket number upon arrival",
        "opening_hours": "Daily: 11:00 AM – 10:00 PM",
        "local_notes": "Created by Gabriele Bonci, the 'Michelangelo of Pizza'."
    },

    # SORRENTO
    {
        "place_id": "it_res_sor_emilia",
        "name": "Trattoria Da Emilia",
        "city_id": "sorrento",
        "city": "Sorrento",
        "neighborhood": "Marina Grande",
        "coordinates": {"lat": 40.6289, "lng": 14.3683},
        "address": "Via Marina Grande, 62, 80067 Sorrento NA, Italy",
        "rating": 4.6,
        "user_ratings_total": 5800,
        "price_level": "€€",
        "cuisine_types": ["Campanian", "Seafood", "Trattoria"],
        "dietary_tier": "naturally_vegetarian",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Handmade Gnocchi alla Sorrentina [VEG]",
            "Spaghetti alla Nerano [VEG]",
            "Insalata Caprese DOP [VEG]",
            "Delizia al Limone Sorrentino [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Walk-in or call 1-2 days ahead",
        "opening_hours": "Daily: 12:00 PM – 3:30 PM, 7:00 PM – 11:00 PM",
        "local_notes": "Family-run since 1947 right on the Marina Grande water's edge."
    },
    {
        "place_id": "it_res_sor_o_parrucchiano",
        "name": "Ristorante O' Parrucchiano La Favorita",
        "city_id": "sorrento",
        "city": "Sorrento",
        "neighborhood": "Corso Italia",
        "coordinates": {"lat": 40.6247, "lng": 14.3719},
        "address": "Corso Italia, 71, 80067 Sorrento NA, Italy",
        "rating": 4.5,
        "user_ratings_total": 7100,
        "price_level": "€€€",
        "cuisine_types": ["Campanian", "Historic Garden Restaurant", "Pasta"],
        "dietary_tier": "vegetarian_friendly",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Original Cannelloni alla Sorrentina [VEG/Meat options]",
            "Ravioli Capresi con Caciotta [VEG]",
            "Melanzane alla Parmigiana [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 3-7 days in advance",
        "opening_hours": "Daily: 12:00 PM – 11:30 PM",
        "local_notes": "Dine under a magnificent historic canopy of fragrant Sorrento lemon groves."
    },
    {
        "place_id": "it_res_sor_franco",
        "name": "Pizzeria Da Franco",
        "city_id": "sorrento",
        "city": "Sorrento",
        "neighborhood": "Piazza Tasso / Station",
        "coordinates": {"lat": 40.6254, "lng": 14.3789},
        "address": "Corso Italia, 265, 80067 Sorrento NA, Italy",
        "rating": 4.5,
        "user_ratings_total": 4200,
        "price_level": "€",
        "cuisine_types": ["Neapolitan Pizza", "Casual Trattoria"],
        "dietary_tier": "naturally_vegetarian",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Pizza Margherita Verace [VEG]",
            "Pizza Marinara Tradizionale [VEG]",
            "Panuozzo Sorrentino [VEG]"
        ],
        "reservation_recommended": False,
        "reservation_urgency": "Casual walk-in",
        "opening_hours": "Daily: 11:30 AM – Midnight",
        "local_notes": "Beloved local pizzeria with rustic wooden communal tables."
    },

    # BARI & PUGLIA
    {
        "place_id": "it_res_bar_le_terrazze",
        "name": "Ristorante Le Terrazze del Santa Lucia",
        "city_id": "bari",
        "city": "Bari",
        "neighborhood": "Lungomare",
        "coordinates": {"lat": 41.1218, "lng": 16.8778},
        "address": "Lungomare Nazario Sauro, 70121 Bari BA, Italy",
        "rating": 4.6,
        "user_ratings_total": 2900,
        "price_level": "€€€",
        "cuisine_types": ["Pugliese", "Seafood", "Pasta"],
        "dietary_tier": "vegetarian_friendly",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Orecchiette con Cime di Rapa [VEG]",
            "Pure di Fave Bianche e Cicoria [VEG]",
            "Burrata di Andria con Pomodorini [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 2-5 days in advance",
        "opening_hours": "Tue-Sun: 12:30 PM – 3:30 PM, 7:30 PM – 11:00 PM",
        "local_notes": "Breathtaking Adriatic sea views along the Lungomare."
    },
    {
        "place_id": "it_res_bar_panificio_fiore",
        "name": "Panificio Fiore 1506",
        "city_id": "bari",
        "city": "Bari",
        "neighborhood": "Bari Vecchia",
        "coordinates": {"lat": 41.1301, "lng": 16.8715},
        "address": "Strada Palazzo di Citta, 38, 70122 Bari BA, Italy",
        "rating": 4.8,
        "user_ratings_total": 4100,
        "price_level": "€",
        "cuisine_types": ["Pugliese Bakery", "Street Food", "Focaccia"],
        "dietary_tier": "naturally_vegetarian",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Authentic Focaccia Barese [VEG]",
            "Panzerotto Fritto con Mozzarella [VEG]",
            "Taralli Pugliesi [VEG]"
        ],
        "reservation_recommended": False,
        "reservation_urgency": "Takeaway counter line",
        "opening_hours": "Mon-Sat: 8:30 AM – 2:30 PM, 5:30 PM – 9:00 PM",
        "local_notes": "Baking inside a 16th-century stone church since 1506."
    },
    {
        "place_id": "it_res_pug_grotta_palazzese",
        "name": "Grotta Palazzese Cave Restaurant",
        "city_id": "puglia",
        "city": "Polignano a Mare",
        "neighborhood": "Old Town Cliffs",
        "coordinates": {"lat": 40.9969, "lng": 17.2185},
        "address": "Via Narciso, 59, 70044 Polignano a Mare BA, Italy",
        "rating": 4.4,
        "user_ratings_total": 5200,
        "price_level": "€€€€",
        "cuisine_types": ["Fine Dining", "Seafood", "Pugliese Gourmet"],
        "dietary_tier": "vegetarian_friendly",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Tasting Menu Vegetariano [VEG]",
            "Risotto all'Acqua di Pomodoro e Burrata [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 30-60 days in advance",
        "opening_hours": "Daily: 12:30 PM – 2:30 PM, 7:00 PM – 11:30 PM (May-Oct)",
        "local_notes": "World-famous restaurant inside a natural marine limestone cave."
    },
    {
        "place_id": "it_res_pug_trullo_d_oro",
        "name": "Ristorante Il Trullo d'Oro",
        "city_id": "puglia",
        "city": "Alberobello",
        "neighborhood": "Trulli District",
        "coordinates": {"lat": 40.7845, "lng": 17.2382},
        "address": "Via Cavallotti, 27, 70011 Alberobello BA, Italy",
        "rating": 4.6,
        "user_ratings_total": 2300,
        "price_level": "€€€",
        "cuisine_types": ["Pugliese", "Traditional Trulli Dining"],
        "dietary_tier": "naturally_vegetarian",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Antipasto Misto Pugliese (Vegetarian selection) [VEG]",
            "Orecchiette al Pomodoro Fresco e Cacioricotta [VEG]",
            "Fave e Foglie con Peperoni Cruschi [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 3-7 days in advance",
        "opening_hours": "Tue-Sun: 12:30 PM – 3:00 PM, 7:30 PM – 10:30 PM",
        "local_notes": "Authentic dining inside five interconnected 18th-century trulli cones."
    },

    # MILAN
    {
        "place_id": "it_res_mil_ratana",
        "name": "Ratana",
        "city_id": "milan",
        "city": "Milan",
        "neighborhood": "Porta Nuova / Isola",
        "coordinates": {"lat": 45.4856, "lng": 9.1912},
        "address": "Via Gaetano de Castillia, 28, 20124 Milano MI, Italy",
        "rating": 4.6,
        "user_ratings_total": 3100,
        "price_level": "€€€",
        "cuisine_types": ["Modern Milanese", "Lombard Cuisine"],
        "dietary_tier": "vegetarian_friendly",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Risotto alla Milanese con Zafferano [VEG]",
            "Cotoletta alla Milanese di Vitello",
            "Verdure dell'Orto con Fonduta [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 14 days in advance",
        "opening_hours": "Daily: 12:30 PM – 2:30 PM, 7:30 PM – 11:00 PM",
        "local_notes": "Located beneath the Bosco Verticale vertical forest."
    },
    {
        "place_id": "it_res_mil_luini",
        "name": "Luini Panzerotti",
        "city_id": "milan",
        "city": "Milan",
        "neighborhood": "Duomo",
        "coordinates": {"lat": 45.4658, "lng": 9.1931},
        "address": "Via Santa Radegonda, 16, 20121 Milano MI, Italy",
        "rating": 4.5,
        "user_ratings_total": 17000,
        "price_level": "€",
        "cuisine_types": ["Street Food", "Bakery", "Panzerotti"],
        "dietary_tier": "naturally_vegetarian",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Panzerotto Fritto Pomodoro e Mozzarella [VEG]",
            "Panzerotto al Forno con Spinaci e Ricotta [VEG]"
        ],
        "reservation_recommended": False,
        "reservation_urgency": "Counter line moves fast",
        "opening_hours": "Mon-Sat: 10:00 AM – 8:00 PM; Sun: 10:30 AM – 7:30 PM",
        "local_notes": "Milanese landmark since 1888, steps from the Duomo."
    },
    {
        "place_id": "it_res_mil_joia",
        "name": "Joia (1 Michelin Star Vegetarian)",
        "city_id": "milan",
        "city": "Milan",
        "neighborhood": "Porta Venezia",
        "coordinates": {"lat": 45.4767, "lng": 9.2062},
        "address": "Via Panfilo Castaldi, 18, 20124 Milano MI, Italy",
        "rating": 4.7,
        "user_ratings_total": 1500,
        "price_level": "€€€€",
        "cuisine_types": ["Fine Dining", "Vegetarian Gourmet", "Haute Cuisine"],
        "dietary_tier": "naturally_vegetarian",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Tasting Menu 'L'Anima e la Natura' [100% VEG]",
            "Arborio rice with saffron, sweet pumpkin and ginger [VEG]",
            "Terrine of roasted wild mushrooms & black truffle [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 3-4 weeks in advance",
        "opening_hours": "Tue-Sat: 7:30 PM – 11:00 PM; Sun-Mon Closed",
        "local_notes": "The first vegetarian restaurant in Europe awarded a Michelin Star."
    },

    # LAKE GARDA
    {
        "place_id": "it_res_gar_la_speranzina",
        "name": "Restaurant La Speranzina Relais & Gourmet",
        "city_id": "lake_garda",
        "city": "Sirmione",
        "neighborhood": "Sirmione Peninsula",
        "coordinates": {"lat": 45.4942, "lng": 10.6071},
        "address": "Via Dante Alighieri, 16, 25019 Sirmione BS, Italy",
        "rating": 4.8,
        "user_ratings_total": 1200,
        "price_level": "€€€€",
        "cuisine_types": ["Fine Dining", "Garda Regional", "Lake Fish & Modern Italian"],
        "dietary_tier": "vegetarian_friendly",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Tortelli di Zucca con Amaretti e Mostarda [VEG]",
            "Risotto al Franciacorta con Tartufo Nero [VEG]",
            "Coregone del Lago alla Plancia"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 2-3 weeks in advance",
        "opening_hours": "Wed-Mon: 12:30 PM – 2:30 PM, 7:30 PM – 10:30 PM",
        "local_notes": "Refined lakeside terrace tables overlooking Lake Garda."
    },
    {
        "place_id": "it_res_gar_trattoria_clementina",
        "name": "Trattoria Clementina",
        "city_id": "lake_garda",
        "city": "Sirmione / Desenzano",
        "neighborhood": "Sirmione Colombare",
        "coordinates": {"lat": 45.4789, "lng": 10.6120},
        "address": "Via San Martino, 18, 25019 Sirmione BS, Italy",
        "rating": 4.6,
        "user_ratings_total": 1900,
        "price_level": "€€",
        "cuisine_types": ["Lombard / Garda Trattoria", "Pasta & Pizza"],
        "dietary_tier": "naturally_vegetarian",
        "vegetarian_friendly": True,
        "signature_dishes": [
            "Tortellini di Valeggio fatti a mano al burro e salvia [VEG]",
            "Bigoli con Salsa di Noci e Ricotta [VEG]",
            "Polenta con Funghi Porcini e Formagella [VEG]"
        ],
        "reservation_recommended": True,
        "reservation_urgency": "Book 1-3 days in advance",
        "opening_hours": "Thu-Tue: 12:00 PM – 2:30 PM, 7:00 PM – 10:30 PM",
        "local_notes": "Warm family-run trattoria known for handmade pasta."
    }
]

REGIONAL_SIGNATURE_DISHES = {
    "rome": [
        {"dish": "Cacio e Pepe", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian", "desc": "Pecorino Romano cheese and freshly cracked black pepper emulsified with starchy pasta water into a creamy glaze."},
        {"dish": "Carciofo alla Giudia", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian", "desc": "Whole Jewish-Roman artichoke twice-fried in olive oil until golden and flower-crisp."},
        {"dish": "Suppli al Telefono", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian (Cheese)", "desc": "Fried rice croquette with tomato sauce and mozzarella center that strings like a telephone wire."},
        {"dish": "Carbonara", "dietary": "meat_heavy", "badge": "🥩 Traditional Meat", "desc": "Classic egg yolk, Pecorino Romano, and crispy cured pork cheek (guanciale). Never with cream."},
        {"dish": "Maritozzo con la Panna", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian Dessert", "desc": "Sweet brioche bun split and generously filled with freshly whipped sweet cream."}
    ],
    "sorrento": [
        {"dish": "Gnocchi alla Sorrentina", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian", "desc": "Soft potato gnocchi baked in terracotta pots with San Marzano tomato sauce, fresh basil, and bubbling stringy fior di latte."},
        {"dish": "Spaghetti alla Nerano", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian", "desc": "Pasta tossed with golden fried sliced zucchini, basil, and sharp local Provolone del Monaco DOP cheese."},
        {"dish": "Insalata Caprese", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian", "desc": "Ripe ox-heart tomatoes, fresh Campania buffalo mozzarella, basil leaves, extra virgin olive oil, and sea salt."},
        {"dish": "Delizia al Limone", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian Dessert", "desc": "Dome-shaped sponge cake soaked in limoncello syrup and coated with luscious lemon custard glaze."}
    ],
    "bari": [
        {"dish": "Orecchiette con Cime di Rapa", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian (Request without anchovy)", "desc": "Handmade 'little ear' pasta with bitter turnip greens, garlic, chili, and toasted breadcrumbs."},
        {"dish": "Focaccia Barese", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian", "desc": "Semolina focaccia baked with boiled potato dough, topped with crushed cherry tomatoes, green olives, and oregano."},
        {"dish": "Panzerotto Fritto", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian", "desc": "Deep-fried dough pocket bursting with bubbling tomato pulp and stringy mozzarella."},
        {"dish": "Tiella Barese (Riso, Patate e Cozze)", "dietary": "pescatarian", "badge": "🐟 Seafood", "desc": "Baked layered terracotta dish of rice, sliced potatoes, fresh Adriatic mussels, and pecorino."}
    ],
    "puglia": [
        {"dish": "Pure di Fave e Cicoria", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian (Vegan)", "desc": "Silky dried fava bean puree served with sauteed wild chicory greens and extra virgin olive oil."},
        {"dish": "Burrata di Andria IGP", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian", "desc": "Mozzarella pouch filled with rich shredded curd and fresh cream (stracciatella)."},
        {"dish": "Pasticciotto Leccese", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian Dessert", "desc": "Warm shortcrust pastry pie filled with rich vanilla-lemon pastry cream."},
        {"dish": "Capocollo di Martina Franca", "dietary": "meat_heavy", "badge": "🥩 Traditional Meat", "desc": "Slow-cured pork collar smoked with fragno oak bark and marinated in cooked wine."}
    ],
    "milan": [
        {"dish": "Risotto alla Milanese", "dietary": "vegetarian_friendly", "badge": "🥗 Vegetarian (Broth check)", "desc": "Carnaroli rice slow-cooked with saffron threads and Parmigiano-Reggiano."},
        {"dish": "Cotoletta alla Milanese", "dietary": "meat_heavy", "badge": "🥩 Traditional Meat", "desc": "Bone-in veal chop breaded and pan-fried to crisp perfection in clarified butter."},
        {"dish": "Mondeghili", "dietary": "meat_heavy", "badge": "🥩 Traditional Meat", "desc": "Historic Milanese fried meatballs made with beef, sausage, mortadella, and lemon zest."},
        {"dish": "Panettone Artigianale", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian Dessert", "desc": "Tall, fluffy sourdough sweet bread studded with candied orange peel, cedar, and raisins."}
    ],
    "lake_garda": [
        {"dish": "Tortellini di Valeggio", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian Options", "desc": "Paper-thin silk pasta knot filled with delicate herbs, pumpkin, or cheeses in melted sage butter."},
        {"dish": "Formagella di Tremosine", "dietary": "naturally_vegetarian", "badge": "🥗 Vegetarian", "desc": "Soft, fragrant mountain pasture cheese produced on the high plateau overlooking Lake Garda."},
        {"dish": "Coregone / Trota del Garda", "dietary": "pescatarian", "badge": "🐟 Lake Fish", "desc": "Freshly caught lake whitefish grilled with DOP Garda olive oil, rosemary, and lemon."},
        {"dish": "Lugana DOC White Wine", "dietary": "naturally_vegetarian", "badge": "🍷 Local Wine", "desc": "Crisp, mineral-driven white wine grown in the clay soils south of Lake Garda around Sirmione."}
    ]
}

TRANSIT_KNOWLEDGE = {
    "sorrento_to_capri_ferry": {
        "departure_port": "Sorrento Marina Piccola",
        "arrival_port": "Capri Marina Grande",
        "duration_minutes": 25,
        "operators": ["Caremar", "NLG", "SNAV"],
        "ticket_price_eur": 22.50,
        "frequency": "Every 30-45 minutes in high season",
        "note": "High-speed hydrofoils operate weather permitting. Pre-booking mandatory during peak summer."
    },
    "sorrento_to_pompeii_train": {
        "line": "Circumvesuviana / Campania Express",
        "departure_station": "Sorrento Stazione",
        "arrival_station": "Pompei Scavi - Villa dei Misteri",
        "duration_minutes": 20,
        "ticket_price_eur": 3.60,
        "frequency": "Every 30 minutes",
        "note": "Campania Express offers air-conditioned guaranteed seats for €8.00."
    },
    "rome_to_milan_high_speed": {
        "line": "Frecciarossa 1000 / Italo",
        "departure_station": "Roma Termini",
        "arrival_station": "Milano Centrale",
        "duration_minutes": 185,
        "ticket_price_eur": 45.00,
        "frequency": "Every 15-20 minutes",
        "note": "Speeds reach 300 km/h. Advance booking secures smart/executive discounts."
    },
    "milan_to_desenzano_garda": {
        "line": "Trenitalia Frecciarossa / Regionale Veloce",
        "departure_station": "Milano Centrale",
        "arrival_station": "Desenzano del Garda-Sirmione",
        "duration_minutes": 52,
        "ticket_price_eur": 9.80,
        "frequency": "Every 30 minutes",
        "note": "From Desenzano station, take local bus LN026 or quick taxi (15 min) into Sirmione old town."
    }
}

with open('knowledge_base/italy_knowledge.py', 'w') as out:
    out.write('# Italy Ground Truth Knowledge Base
')
    out.write('from typing import Dict, List, Any, Optional

')
    out.write('DESTINATIONS = ' + pprint.pformat(DESTINATIONS, indent=4) + '

')
    out.write('PLACES = ' + pprint.pformat(PLACES, indent=4) + '

')
    out.write('RESTAURANTS = ' + pprint.pformat(RESTAURANTS, indent=4) + '

')
    out.write('REGIONAL_SIGNATURE_DISHES = ' + pprint.pformat(REGIONAL_SIGNATURE_DISHES, indent=4) + '

')
    out.write('TRANSIT_KNOWLEDGE = ' + pprint.pformat(TRANSIT_KNOWLEDGE, indent=4) + '
')

print(f'Successfully built knowledge_base/italy_knowledge.py with {len(PLACES)} places, {len(RESTAURANTS)} restaurants.')
