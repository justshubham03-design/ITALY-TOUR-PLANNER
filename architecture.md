# Italy Local Travel Planner — System Architecture & Engineering Blueprint

> **Document Version:** 1.0.0  
> **Status:** Approved / Technical Architecture Document  
> **Frameworks:** LangChain / LangGraph · Google Gemini · Google Maps Platform / MCP · Next.js 15 / React 19  

---

## 1. Architectural Overview & System Topology

The **Italy Local Travel Planner** is an agentic, multi-modal travel intelligence platform designed to eliminate the common pitfalls of modern travel apps: information overload, generic non-executable itineraries, spatial ignorance, and unverified logistics.

The system enforces a strict separation between:
1. **Deterministic Ground Truth Layer:** Google Maps Platform / MCP for exact coordinates, multi-modal transit calculation, and routing; Local Knowledge Base for culinary and cultural facts.
2. **Nondeterministic AI Reasoning Layer:** Google Gemini (via LangChain / LangGraph) for contextual preference parsing, dynamic ranking, multi-day scheduling, and conversational trip editing.
3. **Real-Time Verification Layer:** Web Search Grounding for current ticket availability, booking links, and operational hours.

```mermaid
flowchart TD
    subgraph ClientTier [Frontend Client - Next.js 15 / React 19]
        UI_Home[Home & City Selection]
        UI_Explore[Explore Destination & Category Chips]
        UI_Itinerary[Vertical Timeline & Route View]
        UI_Map[Interactive Map & Clustered Markers]
        UI_Food[Food & Dietary Discovery View]
        UI_Chat[Conversational AI Assistant Drawer]
        UI_Checklist[Reservation & Pre-Trip Checklist]
        ZustandStore[(Zustand State Store + LocalStorage)]
    end

    subgraph BackendGateway [API & Orchestration Gateway - Next.js App Router]
        API_Trip[Trip Planner Controller]
        API_Mutate[Conversational Mutation Controller]
        API_Explore[Explore & Nearby Controller]
        API_Food[Culinary & Dietary Controller]
    end

    subgraph LangChainCore [LangChain & LangGraph Agentic Engine]
        GraphRunner[LangGraph StateGraph Engine]
        StateCheckpoint[(MemorySaver Checkpointer / Redis)]
        LCELChains[LCEL Reasoning Chains & Output Parsers]
        ModelAdapter[ChatGoogleGenerativeAI - Gemini 1.5 Pro / 2.0 Flash]
    end

    subgraph ToolIntegrations [Tool & Ground Truth Layer]
        MCP_Maps[Google Maps MCP / Places & Routes API]
        Tool_Search[Web Search Verification Tool - Tavily / Google Search]
        DB_Local[Local Italian Domain Knowledge DB]
        Tool_Dietary[Vegetarian / Non-Veg Strict Validator]
        Tool_Pacing[Day Load & Fatigue Calculator]
    end

    ClientTier <-->|REST / Server Actions| BackendGateway
    BackendGateway <--> LangChainCore
    LangChainCore <--> ToolIntegrations
    ModelAdapter <--> LangChainCore
```

---

## 2. LangChain & LangGraph Agentic Engine Architecture

### 2.1 StateGraph Workflow Design
Trip planning and natural language itinerary modifications are modeled as a state machine using **LangGraph**. This guarantees deterministic phase execution while retaining cyclic conversational mutability.

```mermaid
stateDiagram-v2
    [*] --> ParsePreferences: User Inputs Trip Criteria
    ParsePreferences --> DiscoverDestinations: Extract Destination, Days, Interests & Diet
    DiscoverDestinations --> FetchMapsGroundTruth: Query POI Candidates
    FetchMapsGroundTruth --> VerifyLiveInformation: Fetch Lat/Lng, Place IDs, Operating Hours
    VerifyLiveInformation --> RankRecommendations: Verify Bookings, Tickets, Closures via Web Search
    RankRecommendations --> ClusterAndOptimizeRoute: Apply 12-Factor Recommendation Scoring
    ClusterAndOptimizeRoute --> GenerateItinerarySchedule: Solve TSP / Geographical Clustering
    GenerateItinerarySchedule --> IntegrateDining: Allocate Realistic Time Slots & Durations
    IntegrateDining --> DetectDayOverload: Match Contextual Midday/Evening Trattorias
    DetectDayOverload --> GenerateReservationChecklist: Evaluate Total Load (Comfortable / Busy / Overloaded)
    GenerateReservationChecklist --> DeliverFinalItinerary: Build Urgency Categorized Checklist
    DeliverFinalItinerary --> AwaitUserInteraction

    AwaitUserInteraction --> MutateItineraryState: User Natural Language Instruction
    MutateItineraryState --> ClusterAndOptimizeRoute: Swap POI / Change Pace / Restructure
    DeliverFinalItinerary --> [*]
```

### 2.2 LangGraph State Schema
```typescript
export interface TripPlanningState {
  // Input constraints
  destination: string;
  durationDays: number;
  startingLocation: string;
  interests: ActivityCategory[];
  foodPreference: "vegetarian" | "non_vegetarian" | "both";
  transportPreference: TransportType[];
  walkingTolerance: "low" | "moderate" | "high";
  dailyAvailabilityHours: number;
  budgetTier: "budget" | "moderate" | "fine_dining" | "luxury";

  // Pipeline intermediate artifacts
  candidatePOIs: DestinationPOI[];
  verifiedPOIs: DestinationPOI[];
  rankedPOIs: DestinationPOI[];
  dailyClusters: Record<number, DestinationPOI[]>;
  candidateRestaurants: Restaurant[];
  dailyItineraries: DailyItinerary[];
  checklist: ReservationChecklist;

  // Execution & Conversation state
  messages: ConversationMessage[];
  dayEfficiencyMap: Record<number, "comfortable" | "busy" | "overloaded">;
  errorWarnings: string[];
}
```

### 2.3 Core LangGraph Nodes & Responsibilities

| Node Name | Function & Execution Logic | Primary Tools Used |
| :--- | :--- | :--- |
| `parse_preferences_node` | Validates and normalizes user constraints; determines if destination is city or regional hub. | Pydantic/Zod Parser |
| `discover_destinations_node` | Queries local repository and Places API for matching attraction candidates. | Local Knowledge DB |
| `fetch_maps_data_node` | Fetches verified coordinates, addresses, opening hours, and place IDs. | Google Maps MCP (Places) |
| `verify_live_info_node` | Live web verification of ticket booking requirements, seasonal closures, and ticket URLs. | Web Search Verification Tool |
| `rank_recommendations_node` | Applies the 12-factor weighting algorithm to compute POI `relevanceScore` and justifications. | Gemini 1.5/2.0 via LCEL |
| `cluster_routes_node` | Solves spatial clustering and order optimization to eliminate backtracking. | Maps Distance Matrix MCP |
| `generate_itinerary_node` | Constructs daily chronological blocks with realistic dwell times and rest pauses. | LangChain Output Parser |
| `integrate_dining_node` | Locates and inserts authentic restaurants near midday and evening attractions based on diet. | Restaurant Dietary Tool |
| `detect_overload_node` | Evaluates total active hours and walking distance; triggers auto-rebalance if overloaded. | Travel Pacing Tool |
| `generate_checklist_node` | Synthesizes pre-trip reservation checklist categorized by urgency (🔴, 🟡, 🟢). | Checklist Synthesizer |
| `mutate_itinerary_node` | Intercepts user chat commands, interprets intent, and updates the itinerary graph. | Gemini Conversational Agent |

---

## 3. Structured Data Models & Schemas

### 3.1 Destination & Point of Interest (POI) Schema
```typescript
export interface DestinationPOI {
  id: string;
  name: string;
  italianName?: string;
  category: ActivityCategory[];
  coordinates: {
    lat: number;
    lng: number;
  };
  address: string;
  popularityScore: number;            // Normalized 0.0 - 1.0
  touristSignificance: "iconic" | "major" | "neighborhood" | "hidden_gem";
  recommendedDurationMinutes: number; // e.g., 90, 150
  openingHours: {
    regular: Record<string, string>;  // e.g., { "monday": "09:00-19:00" }
    seasonalNotes?: string;
    isClosedOn?: string[];            // e.g., ["monday"]
  };
  bookingInfo: {
    isRequired: boolean;
    isRecommended: boolean;
    urgencyLevel: "needs_booking" | "booking_recommended" | "no_booking_required";
    officialBookingUrl?: string;
    estimatedCostEuros?: number;
    bookingAdvanceNoticeDays?: number;
  };
  bestVisitingTime: {
    timeOfDay: "early_morning" | "morning" | "afternoon" | "sunset" | "night";
    reason: string;
  };
  localTips: {
    crowdTip?: string;
    entryTip?: string;
    transitTip?: string;
    foodTip?: string;
  };
  signatureExperience: string;
  relevanceScore: number;             // Dynamic calculation based on user profile
}

export type ActivityCategory =
  | "must_visit"
  | "historical"
  | "museums"
  | "beaches"
  | "shopping"
  | "food"
  | "viewpoints"
  | "nature"
  | "churches"
  | "culture"
  | "photo_spots"
  | "nightlife"
  | "hidden_gems";
```

### 3.2 Restaurant & Culinary Schema
```typescript
export interface Restaurant {
  id: string;
  name: string;
  location: {
    address: string;
    lat: number;
    lng: number;
    distanceFromPreviousPoiMeters: number;
    approxWalkingMinutes: number;
  };
  cuisineType: string[];              // e.g., ["Roman", "Trattoria", "Seafood"]
  priceLevel: "€" | "€€" | "€€€" | "€€€€";
  diningStyle:
    | "breakfast"
    | "lunch"
    | "dinner"
    | "cafe"
    | "fine_dining"
    | "local_traditional"
    | "cheap_eats"
    | "romantic"
    | "family"
    | "quick_meal"
    | "michelin_premium";
  rating: number;                     // 0.0 - 5.0
  reviewCount: number;
  vegetarianSuitability:
    | "vegetarian_focused"            // 100% vegetarian/vegan or dedicated veg menu
    | "vegetarian_friendly"           // Authentic regional vegetarian dishes available
    | "limited_vegetarian"            // Basic side salad / plain pasta only
    | "not_suitable";                 // Meat/seafood broth or lard heavy
  signatureDishes: string[];          // e.g., ["Cacio e Pepe", "Supplì"]
  recommendedDishes: Array<{
    name: string;
    dietary: "vegetarian" | "non_vegetarian" | "depends_on_preparation";
    notes?: string;
  }>;
  openingHours: string;
  bookingRequirement: "mandatory" | "recommended" | "walk_ins_welcome";
  officialBookingUrl?: string;
  googleMapsUrl: string;
}
```

### 3.3 Daily Itinerary & Timeline Schema
```typescript
export interface DailyItinerary {
  dayNumber: number;
  date?: string;
  themeTitle: string;                 // e.g., "Day 2 — Ancient Rome & Trastevere"
  dayEfficiencyStatus: "comfortable" | "busy" | "overloaded";
  metrics: {
    totalTravelTimeMinutes: number;
    totalWalkingDistanceKm: number;
    totalActivityTimeMinutes: number;
    totalMealTimeMinutes: number;
    totalPlannedDayHours: number;
  };
  schedule: ItineraryBlock[];
}

export type ItineraryBlock = ActivityBlock | RestaurantBlock | TransitBlock;

export interface ActivityBlock {
  type: "activity";
  startTime: string;                  // "09:00"
  endTime: string;                    // "11:30"
  durationMinutes: number;
  poi: DestinationPOI;
  actionRequired?: string;
}

export interface RestaurantBlock {
  type: "meal";
  mealType: "breakfast" | "lunch" | "dinner" | "snack_gelato";
  startTime: string;
  endTime: string;
  restaurant: Restaurant;
  suggestedDish: string;
}

export interface TransitBlock {
  type: "transit";
  originName: string;
  destinationName: string;
  distanceMeters: number;
  durationMinutes: number;
  transportMode: TransportType;
  instructions: string;
  googleMapsNavigationUrl: string;
}

export type TransportType = "walking" | "metro" | "bus" | "train" | "ferry" | "taxi" | "car";
```

### 3.4 Reservation Checklist Schema
```typescript
export interface ReservationChecklist {
  tripTitle: string;
  items: ChecklistItem[];
}

export interface ChecklistItem {
  id: string;
  title: string;                      // e.g., "Colosseum Full Experience Pass"
  category: "monument" | "transport" | "restaurant" | "experience" | "hotel";
  urgency: "needs_booking" | "booking_recommended" | "no_booking_required";
  leadTimeGuideline: string;          // e.g., "Book 30 days ahead"
  bookingUrl?: string;
  isCompleted: boolean;
  associatedDay?: number;
}
```

---

## 4. Algorithmic Engines & Domain Logic

### 4.1 The 12-Factor Destination Recommendation Engine
Candidate POIs are evaluated using a deterministic scoring formula synthesized by Gemini and LangChain:

$$\text{RelevanceScore}(POI) = \sum_{i=1}^{12} w_i \cdot s_i(POI)$$

| Factor ($i$) | Weight ($w_i$) | Scoring Metric ($s_i$) |
| :--- | :---: | :--- |
| 1. User Interests Match | 0.20 | Jaccard & semantic cosine similarity with selected interest tags |
| 2. Destination Popularity | 0.10 | Verified rating and global review volume (0.0 to 1.0) |
| 3. Tourist Significance | 0.15 | Iconic = 1.0, Major = 0.8, Neighborhood = 0.5, Hidden Gem = 0.6 |
| 4. Local Relevance | 0.10 | Authenticity score vs. tourist-trap penalty |
| 5. Proximity to Hub / Route | 0.10 | Inverse distance penalty from accommodation or daily cluster center |
| 6. Duration Feasibility | 0.05 | Compatibility with available day budget |
| 7. Opening Hours Match | 0.10 | 1.0 if open during target time window; 0.0 if closed |
| 8. Ticket Availability | 0.05 | 1.0 if tickets verified obtainable; 0.0 if sold out |
| 9. Seasonality Match | 0.05 | Alignment with active travel season (coastal vs. indoor) |
| 10. Weather Adaptability | 0.03 | Weather condition score (indoor bias during rain) |
| 11. Booking Lead Feasibility| 0.04 | Match between required booking lead time and user trip date |
| 12. Geographic Compatibility| 0.03 | Clustering coefficient with preceding and succeeding POIs |

### 4.2 Route Optimization & Anti-Backtracking Engine
To avoid chaotic travel plans, the `cluster_routes_node` utilizes a Traveling Salesperson Problem (TSP) heuristic powered by the Google Maps Distance Matrix API:
1. **K-Means / Spatial Neighborhood Clustering:** Partitions POIs into $N$ clusters (where $N = \text{durationDays}$).
2. **Intra-Day TSP Sequencing:** Sorts POIs within each day to minimize total transit friction:
   $$\min \sum_{j=1}^{k} \text{DistanceMatrix}(\text{Node}_{j-1}, \text{Node}_j)$$
3. **Fixed Reservation Anchors:** Pre-booked timed tickets (e.g. Vatican Museums at 09:30) act as immovable anchor nodes in the sequence.

### 4.3 Day Load Calculation & Overload Detection
$$\text{Total Planned Day} = \sum T_{\text{activities}} + \sum T_{\text{transit}} + \sum T_{\text{meals}} + \sum T_{\text{buffers}}$$

* 🟢 **Comfortable:** $\le 8.0\text{ hours}$, walking $\le 5.0\text{ km}$, $\le 3$ major POIs.
* 🟡 **Busy:** $8.0 - 10.5\text{ hours}$, walking $5.0 - 9.0\text{ km}$, $4$ major POIs.
* 🔴 **Overloaded:** $> 10.5\text{ hours}$ or walking $> 9.0\text{ km}$ or $> 4$ major POIs.
  * *Auto-Rebalancing Heuristic:* Prunes lowest-weight POI, reassigns to subsequent open days, or inserts transit replacements for $>15\text{ min}$ walks.

### 4.4 Restaurant & Dietary Validation Engine
The culinary engine strictly rejects superficial vegetarian tagging:

```
┌─────────────────────────────────────────────────────────────┐
│                 DIETARY SUITABILITY MATRIX                  │
├───────────────────────┬─────────────────────────────────────┤
│ Vegetarian-Focused    │ 100% vegetarian or dedicated menu   │
│ Vegetarian-Friendly   │ Authentic regional veg specialties  │
│ Limited Vegetarian    │ Minimal side salad / fries only     │
│ Not Suitable          │ Meat / seafood broth or lard base   │
└───────────────────────┴─────────────────────────────────────┘
```

---

## 5. API & Interface Specifications

### 5.1 Endpoints Overview

| Method | Route | Description | Engine Handler |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/trips/generate` | Generates a complete multi-day optimized itinerary | LangGraph StateGraph Pipeline |
| `POST` | `/api/trips/chat-mutate` | Executes natural language mutations on an active itinerary | LangChain Conversational Agent |
| `GET`  | `/api/explore/:city` | Retrieves curated category destinations for a city | Destination Discovery Engine |
| `POST` | `/api/explore/nearby` | Computes "Worth the Trip?" nearby destinations | Nearby Recommendation Engine |
| `GET`  | `/api/restaurants/:city` | Retrieves dietary-filtered restaurants | Culinary Engine |
| `GET`  | `/api/trips/:id/checklist` | Retrieves pre-trip reservation checklist | Checklist Generator |

### 5.2 API Contract: Generate Trip (`POST /api/trips/generate`)

#### Request Payload:
```json
{
  "destination": "Sorrento",
  "durationDays": 3,
  "startingLocation": "Grand Hotel Excelsior Vittoria, Sorrento",
  "interests": ["beaches", "historical", "food", "viewpoints", "shopping"],
  "foodPreference": "vegetarian",
  "transportPreference": ["public_transit", "walking", "ferry"],
  "walkingTolerance": "moderate",
  "dailyAvailabilityHours": 9,
  "budgetTier": "moderate"
}
```

#### Response Payload (Sample Output):
```json
{
  "tripId": "trip_sorrento_3d_01",
  "destination": "Sorrento",
  "durationDays": 3,
  "summary": "3-Day Coastal & Historical Journey across Sorrento, Pompeii, and Capri Island",
  "dailyItineraries": [
    {
      "dayNumber": 1,
      "themeTitle": "Day 1 — Sorrento Historic Heart & Marina Grande",
      "dayEfficiencyStatus": "comfortable",
      "metrics": {
        "totalTravelTimeMinutes": 45,
        "totalWalkingDistanceKm": 3.8,
        "totalActivityTimeMinutes": 360,
        "totalMealTimeMinutes": 120,
        "totalPlannedDayHours": 8.75
      },
      "schedule": [
        {
          "type": "activity",
          "startTime": "09:30",
          "endTime": "11:00",
          "durationMinutes": 90,
          "poi": {
            "id": "sorrento_historic_center",
            "name": "Sorrento Historic Centre & Sedil Dominova",
            "category": ["historical", "shopping", "culture"],
            "coordinates": { "lat": 40.6263, "lng": 14.3758 },
            "address": "Via S. Cesareo, 80067 Sorrento NA, Italy",
            "bookingInfo": { "isRequired": false, "urgencyLevel": "no_booking_required" },
            "localTips": { "crowdTip": "Visit morning markets before tourist coaches arrive at 11 AM." }
          }
        },
        {
          "type": "transit",
          "originName": "Sorrento Historic Centre",
          "destinationName": "Marina Grande",
          "distanceMeters": 850,
          "durationMinutes": 12,
          "transportMode": "walking",
          "instructions": "Walk down the historic stone steps through Porta Marina.",
          "googleMapsNavigationUrl": "https://www.google.com/maps/dir/?api=1&origin=40.6263,14.3758&destination=40.6268,14.3687&travelmode=walking"
        },
        {
          "type": "meal",
          "mealType": "lunch",
          "startTime": "12:30",
          "endTime": "14:00",
          "restaurant": {
            "id": "rest_da_emilia",
            "name": "Trattoria da Emilia",
            "cuisineType": ["Campanian", "Traditional Trattoria"],
            "priceLevel": "€€",
            "vegetarianSuitability": "vegetarian_friendly",
            "signatureDishes": ["Gnocchi alla Sorrentina"],
            "googleMapsUrl": "https://maps.google.com/?cid=1234567"
          },
          "suggestedDish": "Handmade Gnocchi alla Sorrentina (Baked with tomato, fresh mozzarella, basil)"
        }
      ]
    }
  ],
  "checklist": {
    "tripTitle": "Sorrento 3-Day Checklist",
    "items": [
      {
        "id": "item_pompeii_ticket",
        "title": "Pompeii Archaeological Site Timed Entry",
        "category": "monument",
        "urgency": "needs_booking",
        "leadTimeGuideline": "Book 14 days in advance",
        "bookingUrl": "http://www.pompeiisites.org/",
        "isCompleted": false,
        "associatedDay": 2
      },
      {
        "id": "item_capri_ferry",
        "title": "High-Speed Ferry: Sorrento to Capri (Morning Departure)",
        "category": "transport",
        "urgency": "booking_recommended",
        "leadTimeGuideline": "Book 3-7 days in advance for summer slots",
        "bookingUrl": "https://www.caremar.it/",
        "isCompleted": false,
        "associatedDay": 3
      }
    ]
  }
}
```

---

## 6. Frontend Architecture & UI Component Hierarchy

### 6.1 Directory Structure (Next.js 15 App Router)
```text
src/
├── app/
│   ├── layout.tsx                     # Root layout with Tailwind & font imports
│   ├── page.tsx                       # Home Screen (Hero & Destination selection)
│   ├── explore/
│   │   └── [city]/page.tsx            # Explore Destination (Category Chips & POI Cards)
│   ├── plan/
│   │   └── page.tsx                   # Itinerary Builder Form
│   ├── itinerary/
│   │   └── [tripId]/page.tsx          # Vertical Timeline & Day Efficiency View
│   ├── map/
│   │   └── page.tsx                   # Interactive Map & Route Polyline View
│   ├── food/
│   │   └── [city]/page.tsx            # Culinary & Dietary Discovery Hub
│   └── checklist/
│       └── [tripId]/page.tsx          # Reservation & Pre-Trip Checklist View
├── components/
│   ├── navigation/
│   │   ├── BottomNav.tsx              # Persistent 5-tab navigation bar
│   │   └── Header.tsx                 # Top navigation with destination indicator
│   ├── itinerary/
│   │   ├── TimelineNode.tsx           # Vertical node with dwell times & action pills
│   │   ├── TransitStep.tsx            # Walk/metro/ferry transit indicator with link
│   │   ├── DayTabSelector.tsx         # Day 1 / Day 2 / Day 3 selector with badges
│   │   └── DayLoadPill.tsx            # Comfortable / Busy / Overloaded badge
│   ├── map/
│   │   ├── MapContainer.tsx           # Google Maps JS API loader wrapper
│   │   ├── ClusteredMarker.tsx        # Categorized POI markers with custom icons
│   │   └── MapBottomSheet.tsx         # Tap-to-inspect place bottom sheet
│   ├── food/
│   │   ├── RestaurantCard.tsx         # Restaurant card with dietary tags & dishes
│   │   └── SignatureDishGrid.tsx      # What should I eat here? regional grid
│   ├── chat/
│   │   ├── ConversationalDrawer.tsx   # AI Assistant chat sidekick
│   │   └── MutationActionCard.tsx     # Preview card for itinerary state changes
│   └── ui/
│       ├── Button.tsx                 # Premium styled buttons
│       ├── Chip.tsx                   # Selectable interest chips
│       └── UrgencyBadge.tsx           # Red / Yellow / Green booking urgency tag
├── lib/
│   ├── langchain/
│   │   ├── graph.ts                   # LangGraph StateGraph definition
│   │   ├── chains.ts                  # LCEL recommendation & scoring chains
│   │   ├── prompts.ts                 # Domain-engineered Italian guide prompts
│   │   └── memory.ts                  # Stateful conversational checkpointers
│   ├── maps/
│   │   ├── client.ts                  # Google Maps API & MCP client wrapper
│   │   └── routing.ts                 # Route & distance matrix utilities
│   ├── db/
│   │   └── italyKnowledge.ts          # Regional signature dishes & destination data
│   └── state/
│       └── useTripStore.ts            # Zustand client state store with persistence
└── types/
    ├── trip.ts                        # TypeScript interfaces for trips & POIs
    └── restaurant.ts                  # Restaurant & dietary interfaces
```

### 6.2 Client State Management (Zustand)
```typescript
import { create } from "zustand";
import { persist } from "zustand/middleware";
import { UserTripPreferences, DailyItinerary, ReservationChecklist, DestinationPOI } from "@/types/trip";

interface TripStoreState {
  preferences: UserTripPreferences;
  activeTripId: string | null;
  activeDayNumber: number;
  itineraries: DailyItinerary[];
  checklist: ReservationChecklist | null;
  selectedPOI: DestinationPOI | null;
  isChatOpen: boolean;
  isLoading: boolean;
  
  // Actions
  setPreferences: (prefs: Partial<UserTripPreferences>) => void;
  setActiveDay: (day: number) => void;
  setSelectedPOI: (poi: DestinationPOI | null) => void;
  toggleChat: () => void;
  setTripData: (itineraries: DailyItinerary[], checklist: ReservationChecklist) => void;
  mutateDayItinerary: (dayNumber: number, updatedDay: DailyItinerary) => void;
}
```

---

## 7. Security, Environment & Deployment Configuration

### 7.1 Environment Variables
```bash
# LLM & LangChain Configuration
GOOGLE_GENAI_API_KEY="AIzaSy..."
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_API_KEY="lsv2_pt_..."
LANGCHAIN_PROJECT="italy-local-travel-planner"

# Google Maps Platform
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY="AIzaSy..."
GOOGLE_MAPS_SERVER_API_KEY="AIzaSy..."

# Web Search Grounding
TAVILY_API_KEY="tvly-..."

# Database & Caching
DATABASE_URL="postgresql://user:pass@localhost:5432/italy_travel"
REDIS_URL="redis://localhost:6379"
```

### 7.2 Anti-Hallucination Guardrails & Fallback Matrix
* **Transit Guardrail:** All transit times must originate from Google Maps MCP / Routes API. If Routes API is unreachable, the system displays estimated walking bounds with an explicit note: *"Estimated walking time (Maps route unavailable)."*
* **Live Verification Guardrail:** If an official booking URL or operating schedule cannot be verified via Web Search, the AI must output: *"Information could not be verified right now. Please verify on-site or via the official venue."*
* **Dietary Guardrail:** If an authentic vegetarian dish cannot be confirmed on a venue’s menu, the venue is classified as `limited_vegetarian` or `not_suitable`.

### 7.3 Caching & Rate Limiting Strategy
* **Google Places & Coordinates:** Cached in Redis / SQLite for 30 days (static geographic coordinates and permanent monuments).
* **Google Routes & Transit Matrix:** Cached for 24 hours per origin/destination/travelmode tuple.
* **Web Search Booking Verification:** Cached for 7 days with forced re-fetch on user booking inquiry.

---

## 8. Summary of Engineering Milestones & Success Criteria

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ENGINEERING MILESTONES                          │
├─────────┬──────────────────────────────────────────────────────────────┤
│ Phase 1 │ Local Knowledge Base & Structured Metadata Schema Setup      │
│ Phase 2 │ LangChain / LangGraph Agentic Pipeline & Gemini Integration │
│ Phase 3 │ Google Maps MCP Integration (Places, Routes, Distance Matrix)│
│ Phase 4 │ Web Search Verification Tool & Live Booking Scraper          │
│ Phase 5 │ Next.js 15 UI / UX (5 Screens, Timeline, Map, Checklist)     │
│ Phase 6 │ End-to-End Testing & Latency Optimization (<5s response)     │
└─────────┴──────────────────────────────────────────────────────────────┘
```

### 8.1 Core Architectural Success Metric
When a user submits:
> *"I’m in Sorrento for 3 days, vegetarian, I like beaches, history, shopping and scenic places."*

The system executes the LangGraph StateGraph pipeline, calls Google Maps MCP and Web Search verification, and returns a strictly typed, geographically clustered 3-day itinerary with exact travel times, verified vegetarian trattorias, local crowd tips, and direct Google Maps navigation in **under 5 seconds**.
