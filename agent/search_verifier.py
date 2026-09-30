"""
Web Search Grounding & Official Booking Verification Layer (Phase 3).
Filters official Italian domain authorities (.va, .it, .gov.it, authorized primary ticket partners)
and classifies ticketing urgency into 🔴 Urgent, 🟡 Advance, and 🟢 Flexible.
"""

import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger('SearchVerifier')

OFFICIAL_AUTHORITY_DOMAINS = [
    'museivaticani.va',
    'colosseo.it',
    'parcocolosseo.it',
    'cenacolovinciano.org',
    'beniculturali.it',
    'cultura.gov.it',
    'gebart.it',
    'museicapitolini.org',
    'pinacotecabrera.org',
    'duomomilano.it',
    'teatroallascala.org',
    'villarufolo.com',
    'funiviedelbaldo.it',
    'vittoriale.it',
    'caremar.it',
    'travelmar.it',
    'ticketone.it',
    'vivaticket.it',
    'coopculture.it'
]

UNVERIFIED_AFFILIATE_PATTERNS = [
    'getyourguide',
    'viator',
    'tiqets',
    'tripadvisor',
    'affiliate',
    'blog',
    'reseller'
]


class SearchVerifier:
    """
    Search Grounding & Ticketing Verification Engine.
    Enforces strict anti-hallucination rules for ticket URLs and operating conditions.
    """

    def __init__(self):
        pass

    def classify_urgency(self, place_name: str, category: str = '', lead_time: str = '') -> Dict[str, Any]:
        """
        Classifies ticketing urgency into 🔴 Urgent, 🟡 Advance, or 🟢 Flexible.
        """
        name_lower = place_name.lower()
        lead_lower = lead_time.lower()

        # High urgency mandatory advance booking sights
        urgent_keywords = [
            'colosseum', 'colosseo', 'vatican', 'sistine', 'last supper', 'cenacolo',
            'galleria borghese', 'capri ferry', 'monte baldo', 'isola del garda', 'grotta palazzese'
        ]
        if any(k in name_lower for k in urgent_keywords) or 'urgent' in lead_lower or '30 days' in lead_lower or '60 days' in lead_lower or '90 days' in lead_lower:
            return {
                'urgency_level': 'urgent',
                'badge': '🔴 Needs Booking (30–90 Days Prior)',
                'tag': 'urgent',
                'requires_advance_booking': True,
                'queue_risk': 'Severe (>2 hours or completely sold out at door)',
                'advice': 'Reserve directly on official platform as soon as slots release.'
            }

        # Advance booking recommended sights
        advance_keywords = [
            'pantheon', 'castel sant', 'capitoline', 'pompeii', 'pompei', 'herculaneum',
            'brera', 'scala', 'prada', 'san siro', 'sforzesco', 'catullo', 'vittoriale',
            'matera', 'castel del monte', 'positano ferry'
        ]
        if any(k in name_lower for k in advance_keywords) or 'advance' in lead_lower or 'week' in lead_lower or 'days prior' in lead_lower:
            return {
                'urgency_level': 'advance',
                'badge': '🟡 Booking Recommended (1–4 Weeks Prior)',
                'tag': 'advance',
                'requires_advance_booking': True,
                'queue_risk': 'Moderate (45-90 min wait during peak season)',
                'advice': 'Book online in advance to secure fast-track entry.'
            }

        # Free / Flexible walk-in sights
        return {
            'urgency_level': 'flexible',
            'badge': '🟢 No Booking Required (Flexible / Walk-in)',
            'tag': 'flexible',
            'requires_advance_booking': False,
            'queue_risk': 'Low / None',
            'advice': 'Walk in freely at your leisure.'
        }

    def verify_booking_url(self, url: str) -> Dict[str, Any]:
        """
        Validates whether a booking link points to an official domain authority or authorized partner.
        """
        if not url:
            return {
                'is_verified': False,
                'is_official': False,
                'disclaimer': 'No direct booking link required for this location.'
            }

        url_lower = url.lower()

        # Check if URL belongs to blacklisted affiliate reseller
        for aff in UNVERIFIED_AFFILIATE_PATTERNS:
            if aff in url_lower:
                return {
                    'is_verified': False,
                    'is_official': False,
                    'disclaimer': 'Third-party reseller link filtered. Please use official municipal authority.'
                }

        # Check if URL belongs to official domain authority
        for official in OFFICIAL_AUTHORITY_DOMAINS:
            if official in url_lower:
                return {
                    'is_verified': True,
                    'is_official': True,
                    'domain': official,
                    'disclaimer': 'Verified official monument / state ticketing portal.'
                }

        # Generic Italian institutional site (.it or .va)
        if '.it/' in url_lower or url_lower.endswith('.it') or '.va/' in url_lower or url_lower.endswith('.va'):
            return {
                'is_verified': True,
                'is_official': True,
                'domain': 'institutional_it',
                'disclaimer': 'Official regional or municipal portal.'
            }

        return {
            'is_verified': False,
            'is_official': False,
            'disclaimer': 'Information could not be verified right now. Verify official portal directly.'
        }

    def verify_poi_operating_status(self, poi: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs holistic verification on a POI profile.
        """
        urgency = self.classify_urgency(
            poi.get('name', ''),
            poi.get('category', ''),
            poi.get('booking_lead_time', '')
        )
        url_verif = self.verify_booking_url(poi.get('official_booking_url', ''))

        return {
            'place_id': poi.get('place_id'),
            'name': poi.get('name'),
            'urgency': urgency,
            'booking_verification': url_verif,
            'verified_official_url': poi.get('official_booking_url', '') if url_verif['is_verified'] else None,
            'anti_hallucination_note': None if url_verif['is_verified'] or not poi.get('official_booking_url') else 'Information could not be verified right now.'
        }
