"""
Extended Detection Module
=========================

Fills in the detection gaps from the v1 feature_matrix + adds AI/CI detection +
implements RevEfficiency Model tier checks.

Imports: used alongside hs_client.HubSpotAuditClient and hs_feature_detect.py
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _status(fid, name, hub, weight="visibility", **kwargs):
    return {
        "id": fid, "name": name, "hub": hub, "weight": weight,
        "in_tier": kwargs.get("in_tier"),
        "configured": kwargs.get("configured", "unknown"),
        "actively_used": kwargs.get("actively_used", "unknown"),
        "used_well": kwargs.get("used_well", "unknown"),
        "notes": kwargs.get("notes", ""),
    }


# =====================================================================
# DETECTION GAP FIXES
# =====================================================================

def detect_sequences(hs, tier_pro: bool) -> Dict[str, Any]:
    """SH-05 — Sequences. Correct endpoint is /automation/v4/flows?type=SEQUENCE or /crm/v3/objects/sequence_enrollments."""
    enrollment_count = 0
    sequence_names = []
    try:
        # HubSpot sequences are exposed via /marketing/v3/transactional or /automation/v4
        # Try the v4 flows endpoint with a SEQUENCE type filter
        result = _safe(lambda: hs._request("GET", "/automation/v4/flows", params={"type": "SEQUENCE", "limit": 100}, note="sequences v4"), default={})
        if isinstance(result, dict) and result.get("results"):
            sequence_names = [r.get("name", "") for r in result["results"]]
    except Exception:
        pass

    # If v4 doesn't work, check for sequence enrollment events via contacts
    if not sequence_names:
        try:
            # Sequences also leave traces on contacts via hs_sequences_is_enrolled
            r = _safe(lambda: hs._request("POST", "/crm/v3/objects/contacts/search",
                json_body={"filterGroups":[{"filters":[{"propertyName":"hs_sequences_is_enrolled","operator":"EQ","value":"true"}]}],"limit":1},
                note="enrolled contacts"), default={})
            enrollment_count = r.get("total", 0) if isinstance(r, dict) else 0
        except Exception:
            pass

    count = len(sequence_names)
    used_well = "yes" if count >= 5 and enrollment_count > 10 else "partial" if count > 0 or enrollment_count > 0 else "no"
    notes = f"{count} sequences detected"
    if enrollment_count:
        notes += f"; {enrollment_count} contacts currently enrolled"
    else:
        notes += "; no current enrollments" if count > 0 else ""

    return _status("SH-05", "Sequences", "sales", "scored",
        in_tier=tier_pro,
        configured="yes" if count > 0 else "no",
        actively_used="yes" if enrollment_count > 0 else "no",
        used_well=used_well,
        notes=notes)


def detect_playbooks(hs, tier_pro: bool) -> Dict[str, Any]:
    """SH-06 — Playbooks. Endpoint: /crm/v3/objects/playbooks or /playbooks/v3."""
    playbook_count = 0
    try:
        # Try CRM object endpoint first
        r = _safe(lambda: hs._request("GET", "/crm/v3/objects/playbooks", params={"limit": 100}, note="playbooks"), default={})
        if isinstance(r, dict):
            playbook_count = len(r.get("results", []))
    except Exception:
        pass

    if playbook_count == 0:
        # Fallback — check legacy playbook endpoint
        try:
            r = _safe(lambda: hs._request("GET", "/playbooks/v3/playbooks", params={"limit": 100}, note="playbooks v3"), default={})
            if isinstance(r, dict):
                playbook_count = len(r.get("results", []))
        except Exception:
            pass

    used_well = "yes" if playbook_count >= 2 else "partial" if playbook_count > 0 else "no"
    return _status("SH-06", "Playbooks", "sales", "scored",
        in_tier=tier_pro,
        configured="yes" if playbook_count > 0 else "no",
        actively_used="yes" if playbook_count > 0 else "no",
        used_well=used_well,
        notes=f"{playbook_count} playbooks detected")


def detect_meeting_links(hs, tier_starter: bool) -> Dict[str, Any]:
    """SH-07 — Meeting scheduler. Endpoint: /scheduler/v3/meetings/meeting-links."""
    link_count = 0
    try:
        r = _safe(lambda: hs._request("GET", "/scheduler/v3/meetings/meeting-links", params={"limit": 100}, note="meeting links"), default={})
        if isinstance(r, dict):
            link_count = len(r.get("results", []))
    except Exception:
        pass

    # Count meetings created in last 90d as usage signal
    meeting_count = 0
    try:
        r = _safe(lambda: hs._request("POST", "/crm/v3/objects/meetings/search",
            json_body={"filterGroups":[{"filters":[{"propertyName":"hs_meeting_start_time","operator":"GT","value":"2026-01-23"}]}],"limit":1},
            note="meeting count"), default={})
        meeting_count = r.get("total", 0) if isinstance(r, dict) else 0
    except Exception:
        pass

    used_well = "yes" if link_count >= 3 and meeting_count > 30 else "partial" if link_count > 0 or meeting_count > 0 else "no"
    return _status("SH-07", "Meeting scheduler / links", "sales", "scored",
        in_tier=tier_starter,
        configured="yes" if link_count > 0 else "no",
        actively_used="yes" if meeting_count > 10 else "partial" if meeting_count > 0 else "no",
        used_well=used_well,
        notes=f"{link_count} scheduler link(s); {meeting_count} meetings in last 90d")


def detect_forecast(hs, tier_pro: bool) -> Dict[str, Any]:
    """SH-08 — Forecast tool. Endpoint: /crm/v3/objects/forecast_submissions or /forecast/v3."""
    submission_count = 0
    try:
        # Try forecast submissions
        r = _safe(lambda: hs._request("GET", "/crm/v3/objects/forecast_submissions", params={"limit": 100}, note="forecast submissions"), default={})
        if isinstance(r, dict):
            submission_count = len(r.get("results", []))
    except Exception:
        pass

    used_well = "yes" if submission_count >= 10 else "partial" if submission_count > 0 else "no"
    return _status("SH-08", "Forecast tool", "sales", "scored",
        in_tier=tier_pro,
        configured="yes" if submission_count > 0 else "no",
        actively_used="yes" if submission_count > 5 else "partial" if submission_count > 0 else "no",
        used_well=used_well,
        notes=f"{submission_count} forecast submission(s) detected" if submission_count else "No forecast submissions — tool appears unused")


def detect_templates(hs, tier_pro: bool) -> Dict[str, Any]:
    """SH-11 — Email templates. Endpoint: /marketing/v3/transactional/single-email-template or /crm/v3/objects/email_templates."""
    template_count = 0
    try:
        # Try templates endpoint
        r = _safe(lambda: hs._request("GET", "/crm/v3/objects/email_templates", params={"limit": 100}, note="templates"), default={})
        if isinstance(r, dict):
            template_count = len(r.get("results", []))
    except Exception:
        pass

    return _status("SH-11", "Email templates", "sales", "visibility",
        in_tier=tier_pro,
        configured="yes" if template_count > 0 else "no",
        actively_used="unknown",
        used_well="yes" if template_count >= 10 else "partial" if template_count > 0 else "no",
        notes=f"{template_count} template(s) detected")


def detect_snippets(hs) -> Dict[str, Any]:
    """SH-12 — Snippets. Endpoint: /crm/v3/objects/snippets."""
    snippet_count = 0
    try:
        r = _safe(lambda: hs._request("GET", "/crm/v3/objects/snippets", params={"limit": 100}, note="snippets"), default={})
        if isinstance(r, dict):
            snippet_count = len(r.get("results", []))
    except Exception:
        pass

    return _status("SH-12", "Snippets", "sales", "visibility",
        in_tier=True,
        configured="yes" if snippet_count > 0 else "no",
        actively_used="unknown",
        used_well="yes" if snippet_count >= 5 else "partial" if snippet_count > 0 else "no",
        notes=f"{snippet_count} snippet(s) detected")


def detect_quotes(hs, tier_starter: bool) -> Dict[str, Any]:
    """SH-14 — Quotes. Endpoint: /crm/v3/objects/quotes."""
    quote_count = 0
    recent_count = 0
    try:
        r = _safe(lambda: hs._request("GET", "/crm/v3/objects/quotes", params={"limit": 1}, note="quotes"), default={})
        quote_count = r.get("total", 0) if isinstance(r, dict) else 0
        # Recent
        r2 = _safe(lambda: hs._request("POST", "/crm/v3/objects/quotes/search",
            json_body={"filterGroups":[{"filters":[{"propertyName":"hs_createdate","operator":"GT","value":"2026-01-23"}]}],"limit":1},
            note="quotes 90d"), default={})
        recent_count = r2.get("total", 0) if isinstance(r2, dict) else 0
    except Exception:
        pass

    return _status("SH-14", "Quotes", "sales", "visibility",
        in_tier=tier_starter,
        configured="yes" if quote_count > 0 else "no",
        actively_used="yes" if recent_count > 5 else "partial" if recent_count > 0 else "no",
        used_well="yes" if recent_count >= 10 else "partial" if recent_count > 0 else "no",
        notes=f"{quote_count} total quotes; {recent_count} in last 90d")


def detect_marketing_emails(hs, tier_starter: bool) -> Dict[str, Any]:
    """MH-01 — Marketing emails. Endpoint: /marketing/v3/emails."""
    email_count = 0
    recent_sent = 0
    try:
        # List marketing emails
        r = _safe(lambda: hs._request("GET", "/marketing/v3/emails", params={"limit": 100}, note="marketing emails"), default={})
        if isinstance(r, dict):
            emails = r.get("results", [])
            email_count = len(emails)
            # Count ones sent in last 90d
            for e in emails:
                pub = e.get("publishDate") or e.get("created")
                if pub and pub > "2026-01-23":
                    recent_sent += 1
    except Exception:
        pass

    used_well = "yes" if email_count >= 10 and recent_sent >= 3 else "partial" if email_count > 0 else "no"
    return _status("MH-01", "Marketing emails", "marketing", "scored",
        in_tier=tier_starter,
        configured="yes" if email_count > 0 else "no",
        actively_used="yes" if recent_sent > 0 else "no",
        used_well=used_well,
        notes=f"{email_count} marketing emails; {recent_sent} published in last 90d")


def detect_landing_pages(hs, tier_starter: bool) -> Dict[str, Any]:
    """MH-03 — Landing pages. Endpoint: /cms/v3/pages/landing-pages."""
    page_count = 0
    try:
        r = _safe(lambda: hs._request("GET", "/cms/v3/pages/landing-pages", params={"limit": 100}, note="landing pages"), default={})
        if isinstance(r, dict):
            page_count = len(r.get("results", []))
    except Exception:
        pass

    used_well = "yes" if page_count >= 5 else "partial" if page_count > 0 else "no"
    return _status("MH-03", "Landing pages", "marketing", "scored",
        in_tier=tier_starter,
        configured="yes" if page_count > 0 else "no",
        actively_used="yes" if page_count > 0 else "no",
        used_well=used_well,
        notes=f"{page_count} landing page(s) detected")


def detect_knowledge_base(hs, tier_pro: bool) -> Dict[str, Any]:
    """SVH-03 — Knowledge base. Endpoint: /cms/v3/knowledge-base/articles."""
    article_count = 0
    try:
        r = _safe(lambda: hs._request("GET", "/cms/v3/knowledge-base/articles", params={"limit": 100}, note="KB articles"), default={})
        if isinstance(r, dict):
            article_count = len(r.get("results", []))
    except Exception:
        pass

    used_well = "yes" if article_count >= 20 else "partial" if article_count > 0 else "no"
    return _status("SVH-03", "Knowledge base", "service", "scored",
        in_tier=tier_pro,
        configured="yes" if article_count > 0 else "no",
        actively_used="yes" if article_count > 5 else "partial" if article_count > 0 else "no",
        used_well=used_well,
        notes=f"{article_count} KB article(s)")


def detect_social_posts(hs, tier_pro: bool) -> Dict[str, Any]:
    """MH-09 augment — check if social posts are being published, not just accounts connected."""
    posts_count = 0
    try:
        r = _safe(lambda: hs._request("GET", "/marketing/v3/social/broadcasts", params={"limit": 100}, note="social broadcasts"), default={})
        if isinstance(r, dict):
            posts_count = len(r.get("results", []))
    except Exception:
        pass
    return {"social_posts_90d": posts_count, "source": "broadcasts API"}


def detect_ad_campaigns(hs, tier_pro: bool) -> Dict[str, Any]:
    """MH-08 augment — check actual ad spend/campaigns, not just accounts."""
    campaign_count = 0
    try:
        r = _safe(lambda: hs._request("GET", "/marketing/v3/ads/campaigns", params={"limit": 100}, note="ad campaigns"), default={})
        if isinstance(r, dict):
            campaign_count = len(r.get("results", []))
    except Exception:
        pass
    return {"ad_campaigns": campaign_count, "source": "ads API"}


# =====================================================================
# AI DETECTION
# =====================================================================

def detect_ai_features(hs, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Comprehensive AI & Automation audit per ai_utilization.md."""
    features = []

    mkt_pro = profile.get("marketing_hub_tier") in ("professional", "enterprise")
    sales_pro = profile.get("sales_hub_tier") in ("professional", "enterprise")
    service_pro = profile.get("service_hub_tier") in ("professional", "enterprise")
    ops_pro = profile.get("ops_hub_tier") in ("professional", "enterprise")

    # Pre-fetch data for AI detection
    contact_props = _safe(lambda: hs.list_properties("contacts"), default=[]) or []
    company_props = _safe(lambda: hs.list_properties("companies"), default=[]) or []
    workflows = _safe(lambda: hs.list_all_workflows(), default=[]) or []
    workflow_names_low = [(w.get("name") or "").lower() for w in workflows]

    # -------- Breeze features --------
    # BR-01 Copilot
    has_chat_props = any("chat_assistant" in (p.get("name") or "").lower() for p in contact_props)
    features.append(_status("BR-01", "Breeze Copilot", "breeze", "scored",
        in_tier=True,
        configured="yes" if has_chat_props else "unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Chat Assistant properties present in data model" if has_chat_props else "No Copilot indicators in property schema"))

    # BR-02 Prospecting Agent
    has_prospecting = any("prospecting_agent" in (p.get("name") or "").lower() for p in company_props)
    features.append(_status("BR-02", "Breeze Prospecting Agent", "breeze", "scored",
        in_tier=sales_pro,
        configured="yes" if has_prospecting else "no",
        actively_used="yes" if has_prospecting else "no",
        used_well="unknown",
        notes="Prospecting agent properties active on Company records" if has_prospecting else "Prospecting agent not in use"))

    # BR-03 Content Agent
    features.append(_status("BR-03", "Breeze Content Agent", "breeze", "visibility",
        in_tier=mkt_pro,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Detection requires marketing email metadata scan — manual check recommended"))

    # BR-04 Customer Agent
    features.append(_status("BR-04", "Breeze Customer Agent", "breeze", "scored",
        in_tier=service_pro,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Requires Service Pro+ and conversations inbox review"))

    # BR-05 Fit Score
    fit_workflows = [n for n in workflow_names_low if "fit score" in n]
    features.append(_status("BR-05", "AI Fit Score", "breeze", "scored",
        in_tier=mkt_pro,
        configured="yes" if fit_workflows else "unknown",
        actively_used="yes" if fit_workflows else "unknown",
        used_well="unknown",
        notes=f"{len(fit_workflows)} workflow(s) keyed off Fit Score" if fit_workflows else "Fit Score usage not detected in workflows"))

    # BR-06 Engagement Score
    eng_workflows = [n for n in workflow_names_low if "engagement score" in n]
    features.append(_status("BR-06", "AI Engagement Score", "breeze", "scored",
        in_tier=mkt_pro,
        configured="yes" if eng_workflows else "unknown",
        actively_used="yes" if eng_workflows else "unknown",
        used_well="unknown",
        notes=f"{len(eng_workflows)} workflow(s) keyed off Engagement Score" if eng_workflows else "Engagement Score usage not detected"))

    # BR-07 Predictive Lead Scoring (Enterprise only)
    predictive_props = [p for p in contact_props if "predictive" in (p.get("name") or "").lower() or "hubspotscore_enterprise" in (p.get("name") or "").lower()]
    ent_tier = profile.get("marketing_hub_tier") == "enterprise"
    features.append(_status("BR-07", "Predictive Lead Scoring", "breeze", "scored",
        in_tier=ent_tier,
        configured="yes" if predictive_props else "no",
        actively_used="unknown",
        used_well="unknown",
        notes=f"{len(predictive_props)} predictive scoring properties" if predictive_props else "Not configured"))

    # BR-08 AI Workflow actions (heuristic only — hard to detect without action-level inspection)
    features.append(_status("BR-08", "AI Workflow actions", "breeze", "scored",
        in_tier=mkt_pro or ops_pro,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Requires workflow action-level inspection — manual check recommended"))

    # -------- Third-party AI --------
    # AI-01 Claude / MCP detection
    # Claude connector would show via installed apps or API usage logs; no direct API
    features.append(_status("AI-01", "Claude connector (MCP)", "ai_integration", "visibility",
        in_tier=True,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Detection requires OAuth grants inspection or installed apps API — manual check recommended"))

    # AI-02 OpenAI / ChatGPT
    features.append(_status("AI-02", "OpenAI / ChatGPT integration", "ai_integration", "visibility",
        in_tier=True,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Detection requires installed apps inspection"))

    # -------- Conversation Intelligence --------
    # Heuristic: look for CI tool references in workflow names
    ci_tools_detected = []
    ci_keywords = {
        "gong": "Gong",
        "chorus": "Chorus",
        "fireflies": "Fireflies",
        "otter": "Otter",
        "grain": "Grain",
        "fathom": "Fathom",
        "read.ai": "Read.ai",
        "read ai": "Read.ai",
        "abstrakt": "Abstrakt",
    }
    for name in workflow_names_low:
        for kw, label in ci_keywords.items():
            if kw in name and label not in ci_tools_detected:
                ci_tools_detected.append(label)

    # CI-01 Gong
    features.append(_status("CI-01", "Gong (conversation intelligence)", "ci", "scored",
        in_tier=True,
        configured="yes" if "Gong" in ci_tools_detected else "no",
        actively_used="yes" if "Gong" in ci_tools_detected else "no",
        used_well="unknown",
        notes=f"Gong integration detected via workflow names" if "Gong" in ci_tools_detected else "Not detected"))

    # CI-04 Zoom AI Companion
    # Heuristic: Zoom meetings with AI-generated summaries (requires meeting notes inspection)
    features.append(_status("CI-04", "Zoom AI Companion", "ci", "visibility",
        in_tier=True,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Detection requires meeting body content analysis"))

    # CI catch-all
    other_ci = [t for t in ci_tools_detected if t not in ("Gong",)]
    if other_ci:
        features.append(_status("CI-0x", "Other CI tools detected", "ci", "scored",
            in_tier=True,
            configured="yes",
            actively_used="yes",
            used_well="unknown",
            notes=f"Detected: {', '.join(other_ci)}"))

    # Dual-engagement detection — auto-critical if Zoom AI AND Read/Fireflies both present
    if ("Read.ai" in ci_tools_detected or "Fireflies" in ci_tools_detected) and True:  # Zoom is default assumed
        features.append(_status("AP-15", "DUAL-ENGAGEMENT RISK", "ci", "scored",
            in_tier=True,
            configured="yes",
            actively_used="yes",
            used_well="no",
            notes="Multiple meeting AI tools detected — risk of duplicate engagement logging"))

    return features


# =====================================================================
# REVEFFICIENCY MODEL TIER AUDIT
# =====================================================================

def audit_keep_tier(hs, profile, lists, workflows, company_props) -> Dict[str, Any]:
    """Tier 1: KEEP — retain current clients."""
    deductions = []

    lists_low = [(l.get("name") or "").lower() for l in lists]
    wf_names_low = [(w.get("name") or "").lower() for w in workflows]
    prop_names_low = [(p.get("name") or "").lower() for p in company_props]

    # QBR tracking
    has_qbr = any("qbr" in n or "quarterly review" in n for n in prop_names_low) or \
              any("qbr" in n or "quarterly review" in n for n in lists_low)
    if not has_qbr:
        deductions.append({"element": "QBR tracking", "severity": "high", "amount": -8, "notes": "No QBR properties or lists detected"})

    # Lease-end / contract-end on company or deal
    has_lease = any(any(k in n for k in ("lease_end", "lease_expir", "contract_end", "contract_expir", "renewal_date")) for n in prop_names_low)
    if not has_lease:
        deductions.append({"element": "Lease/contract end tracking", "severity": "critical", "amount": -15, "notes": "No lease/contract-end properties — blocking for dealer-channel renewal motion"})

    # Dormant customer list
    has_dormant = any(("dormant" in n) or ("no activity" in n and "customer" in n) for n in lists_low)
    if not has_dormant:
        deductions.append({"element": "Dormant customer detection", "severity": "medium", "amount": -3, "notes": "No 'dormant customer' or 'customer no activity' list detected"})

    # Customer lifecycle distinct from prospect
    # Proxy: lifecycle stage property exists (always will) — harder to check distinctness
    # Skip unless we have deeper access

    # Renewal workflow
    has_renewal_wf = any("renewal" in n for n in wf_names_low)
    if not has_renewal_wf and has_lease:
        deductions.append({"element": "Renewal workflow", "severity": "critical", "amount": -15, "notes": "Lease-end properties exist but no renewal workflow triggered off them"})
    elif not has_renewal_wf:
        deductions.append({"element": "Renewal workflow", "severity": "high", "amount": -8, "notes": "No renewal workflow detected"})

    total = sum(d["amount"] for d in deductions)
    score = max(0, 100 + total)
    return {"tier": "KEEP", "score": score, "deductions": deductions}


def audit_grow_tier(hs, profile, lists, workflows) -> Dict[str, Any]:
    """Tier 2: GROW — expand inside accounts."""
    deductions = []

    lists_low = [(l.get("name") or "").lower() for l in lists]
    wf_names_low = [(w.get("name") or "").lower() for w in workflows]

    # Cross-sell lists
    xsell_lists = [n for n in lists_low if "cross-sell" in n or "cross sell" in n or "xsell" in n]
    if not xsell_lists:
        deductions.append({"element": "Cross-sell segmentation lists", "severity": "high", "amount": -8, "notes": "No cross-sell lists detected"})

    # Upsell lists or workflows
    upsell_items = [n for n in (lists_low + wf_names_low) if "upsell" in n or "up-sell" in n or "up sell" in n]
    if not upsell_items:
        deductions.append({"element": "Upsell motion", "severity": "high", "amount": -8, "notes": "No upsell lists or workflows detected"})

    # Re-sell / expansion signals
    has_expansion = any("expansion" in n or "resell" in n or "re-sell" in n for n in (lists_low + wf_names_low))
    if not has_expansion:
        deductions.append({"element": "Re-sell / expansion tracking", "severity": "medium", "amount": -3, "notes": "No expansion/re-sell structure detected"})

    total = sum(d["amount"] for d in deductions)
    score = max(0, 100 + total)
    return {"tier": "GROW", "score": score, "deductions": deductions}


def audit_multiply_tier(hs, profile, lists, workflows) -> Dict[str, Any]:
    """Tier 3: MULTIPLY — referrals and networks."""
    deductions = []

    lists_low = [(l.get("name") or "").lower() for l in lists]
    wf_names_low = [(w.get("name") or "").lower() for w in workflows]

    # Referral program
    has_referral = any("referral" in n for n in (lists_low + wf_names_low))
    if not has_referral:
        deductions.append({"element": "Referral program structure", "severity": "high", "amount": -8, "notes": "No referral lists or workflows detected"})

    # Former customer tracking
    has_former = any("former" in n and ("customer" in n or "client" in n) for n in lists_low)
    if not has_former:
        deductions.append({"element": "Former customer / job-change tracking", "severity": "medium", "amount": -3, "notes": "No 'former customer' list detected"})

    # LinkedIn integration — heuristic check
    has_linkedin_signal = any("linkedin" in n for n in (lists_low + wf_names_low))
    if not has_linkedin_signal:
        deductions.append({"element": "LinkedIn integration signals", "severity": "medium", "amount": -3, "notes": "No LinkedIn Sales Navigator indicators detected"})

    total = sum(d["amount"] for d in deductions)
    score = max(0, 100 + total)
    return {"tier": "MULTIPLY", "score": score, "deductions": deductions}


def audit_convert_tier(hs, profile, lists, workflows) -> Dict[str, Any]:
    """Tier 4: CONVERT — largest tier, re-engage warm/missed opportunities."""
    deductions = []

    lists_low = [(l.get("name") or "").lower() for l in lists]
    wf_names_low = [(w.get("name") or "").lower() for w in workflows]

    # The 17 required lists from the Sales Blitz playbook
    required_lists = {
        "Stalled Deals": ["stalled deal", "stalled deals", "aged in stage"],
        "Former Clients": ["former client", "former customer", "win-back", "winback"],
        "Past Meetings - No Deal": ["past meeting", "meeting no deal"],
        "Lost Deals": ["lost deal", "closed lost", "closed-lost"],
        "MQLs": ["mql", "marketing qualified"],
        "SQLs": ["sql", "sales qualified"],
        "Form submissions": ["form submission"],
        "Contact Us": ["contact us"],
        "Leads not contacted 30/60/90": ["not contacted", "no contact in"],
        "Open Deals": ["open deal", "active deal", "pipeline"],
        "No follow-up 30/60/90": ["no follow-up", "no followup", "no activity"],
        "Website visitor leads": ["website visitor", "visited website", "web visit"],
        "Follow-ups": ["follow-up", "followup"],
        "No-shows": ["no-show", "no show"],
        "Trade show attendees": ["trade show", "tradeshow", "event attendee"],
    }

    # Auto-critical checks
    has_stalled = any(any(kw in n for kw in required_lists["Stalled Deals"]) for n in lists_low)
    if not has_stalled:
        deductions.append({"element": "Stalled Deals list (auto-critical)", "severity": "critical", "amount": -15, "notes": "Most important CONVERT list — single biggest revenue leak if missing"})

    has_no_contact = any(any(kw in n for kw in required_lists["Leads not contacted 30/60/90"]) for n in lists_low)
    if not has_no_contact:
        deductions.append({"element": "Leads not contacted 30/60/90 (auto-critical)", "severity": "critical", "amount": -15, "notes": "Lead leakage indicator — required for follow-up discipline"})

    # For other required lists, deduct per missing (capped)
    other_required = [k for k in required_lists if k not in ("Stalled Deals", "Leads not contacted 30/60/90")]
    missing_count = 0
    missing_names = []
    for key in other_required:
        keywords = required_lists[key]
        if not any(any(kw in n for kw in keywords) for n in lists_low):
            missing_count += 1
            missing_names.append(key)

    if missing_count > 0:
        per_missing = -2
        total_missing = max(-20, per_missing * missing_count)  # cap at -20
        deductions.append({"element": f"{missing_count} other required CONVERT lists missing", "severity": "medium", "amount": total_missing, "notes": f"Missing: {', '.join(missing_names[:6])}{'...' if len(missing_names) > 6 else ''}"})

    # Workflows
    has_mql_sql_handoff = any("mql" in n and ("sql" in n or "hand" in n) for n in wf_names_low)
    if not has_mql_sql_handoff:
        deductions.append({"element": "MQL → SQL handoff automation", "severity": "high", "amount": -8, "notes": "No MQL/SQL transition workflow detected"})

    has_reassign = any("reassign" in n and ("lead" in n or "no response" in n) for n in wf_names_low)
    if not has_reassign:
        deductions.append({"element": "Lead reassignment on no-response", "severity": "high", "amount": -8, "notes": "No lead reassignment workflow detected"})

    has_stalled_alert = any("stalled" in n and ("alert" in n or "notify" in n) for n in wf_names_low)
    if not has_stalled_alert:
        deductions.append({"element": "Stalled deal alert workflow", "severity": "high", "amount": -8, "notes": "No stalled deal alerting workflow detected"})

    total = sum(d["amount"] for d in deductions)
    score = max(0, 100 + total)
    return {"tier": "CONVERT", "score": score, "deductions": deductions, "missing_list_count": missing_count + (0 if has_stalled else 1) + (0 if has_no_contact else 1)}


def audit_expand_tier(hs, profile, lists, workflows, contact_props, company_props) -> Dict[str, Any]:
    """Tier 5: EXPAND — net new clients."""
    deductions = []

    lists_low = [(l.get("name") or "").lower() for l in lists]
    wf_names_low = [(w.get("name") or "").lower() for w in workflows]
    contact_prop_names = [(p.get("name") or "").lower() for p in contact_props]
    company_prop_names = [(p.get("name") or "").lower() for p in company_props]

    # ICP property
    has_icp = any("icp" in n or "ideal_customer" in n or "ideal customer" in n for n in (contact_prop_names + company_prop_names))
    if not has_icp:
        deductions.append({"element": "ICP property definition", "severity": "critical", "amount": -15, "notes": "No ICP (Ideal Customer Profile) property detected on Contact or Company"})
    else:
        # Property exists — check fill rate
        try:
            fill = hs.property_fill_rate("companies", "hs_ideal_customer_profile", sample_size=200) if any("hs_ideal_customer_profile" in n for n in company_prop_names) else None
            if fill and (fill.get("rate") or 0) < 0.4:
                deductions.append({"element": "ICP property fill rate", "severity": "high", "amount": -8, "notes": f"ICP property exists but fill rate is {(fill.get('rate') or 0)*100:.0f}% (< 40%)"})
        except Exception:
            pass

    # Persona property
    has_persona = any("persona" in n for n in (contact_prop_names + company_prop_names))
    if not has_persona:
        deductions.append({"element": "Persona property", "severity": "high", "amount": -8, "notes": "No persona property detected"})

    # Target Accounts
    has_target_account = any("target_account" in n or "is_target_account" in n for n in company_prop_names)
    target_count = 0
    if has_target_account:
        try:
            r = _safe(lambda: hs._request("POST", "/crm/v3/objects/companies/search",
                json_body={"filterGroups":[{"filters":[{"propertyName":"hs_is_target_account","operator":"EQ","value":"true"}]}],"limit":1},
                note="target accounts"), default={})
            target_count = r.get("total", 0) if isinstance(r, dict) else 0
        except Exception:
            pass
        if target_count == 0:
            deductions.append({"element": "Target Accounts (ABM)", "severity": "high", "amount": -8, "notes": "Target Accounts property exists but 0 companies flagged"})
    else:
        deductions.append({"element": "Target Accounts (ABM) configuration", "severity": "high", "amount": -8, "notes": "Target Accounts not configured"})

    # Persona trigger lists
    has_persona_lists = any("persona" in n for n in lists_low)
    if not has_persona_lists and has_persona:
        deductions.append({"element": "Persona trigger lists", "severity": "high", "amount": -8, "notes": "Persona property exists but no persona-based lists detected"})

    # ZoomInfo intent
    has_zi_intent = any(("zoominfo" in n or "intent" in n) for n in (lists_low + wf_names_low))
    if not has_zi_intent:
        deductions.append({"element": "Intent-based lists (ZoomInfo intent/scoops)", "severity": "medium", "amount": -3, "notes": "No ZoomInfo intent or scoops signals detected in lists/workflows"})

    total = sum(d["amount"] for d in deductions)
    score = max(0, 100 + total)
    return {"tier": "EXPAND", "score": score, "deductions": deductions, "target_account_count": target_count}


def audit_revenue_efficiency(hs, profile) -> Dict[str, Any]:
    """Run the full 5-tier RevEfficiency audit."""
    # Pre-fetch shared data
    lists = _safe(lambda: hs.list_all_lists(), default=[]) or []
    workflows = _safe(lambda: hs.list_all_workflows(), default=[]) or []
    contact_props = _safe(lambda: hs.list_properties("contacts"), default=[]) or []
    company_props = _safe(lambda: hs.list_properties("companies"), default=[]) or []

    keep = audit_keep_tier(hs, profile, lists, workflows, company_props)
    grow = audit_grow_tier(hs, profile, lists, workflows)
    multiply = audit_multiply_tier(hs, profile, lists, workflows)
    convert = audit_convert_tier(hs, profile, lists, workflows)
    expand = audit_expand_tier(hs, profile, lists, workflows, contact_props, company_props)

    tiers = [keep, grow, multiply, convert, expand]
    tier_scores = [t["score"] for t in tiers]
    overall = min(tier_scores)
    limiting = tiers[tier_scores.index(overall)]["tier"]

    return {
        "overall_score": overall,
        "limiting_tier": limiting,
        "tier_scores": {t["tier"]: t["score"] for t in tiers},
        "tier_detail": {t["tier"]: t for t in tiers},
    }


# =====================================================================
# ORCHESTRATOR
# =====================================================================

def run_extended_detection(hs, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Run the full extended detection pass: gap fixes + AI + RevEfficiency."""
    sales_pro = profile.get("sales_hub_tier") in ("professional", "enterprise")
    sales_starter = profile.get("sales_hub_tier") in ("starter", "professional", "enterprise")
    mkt_pro = profile.get("marketing_hub_tier") in ("professional", "enterprise")
    mkt_starter = profile.get("marketing_hub_tier") in ("starter", "professional", "enterprise")
    svc_pro = profile.get("service_hub_tier") in ("professional", "enterprise")

    results = {
        "gap_fixes": {
            "sequences": detect_sequences(hs, sales_pro),
            "playbooks": detect_playbooks(hs, sales_pro),
            "meeting_links": detect_meeting_links(hs, sales_starter),
            "forecast": detect_forecast(hs, sales_pro),
            "templates": detect_templates(hs, sales_pro),
            "snippets": detect_snippets(hs),
            "quotes": detect_quotes(hs, sales_starter),
            "marketing_emails": detect_marketing_emails(hs, mkt_starter),
            "landing_pages": detect_landing_pages(hs, mkt_starter),
            "knowledge_base": detect_knowledge_base(hs, svc_pro),
            "social_posts": detect_social_posts(hs, mkt_pro),
            "ad_campaigns": detect_ad_campaigns(hs, mkt_pro),
        },
        "ai_features": detect_ai_features(hs, profile),
        "revenue_efficiency": audit_revenue_efficiency(hs, profile),
    }
    return results


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from hs_client import HubSpotAuditClient

    tok = os.environ.get("HUBSPOT_PRIVATE_APP_TOKEN")
    if not tok:
        print("Set HUBSPOT_PRIVATE_APP_TOKEN"); sys.exit(1)

    hs = HubSpotAuditClient(tok)
    profile = {
        "sales_hub_tier": "professional",
        "marketing_hub_tier": "professional",
        "service_hub_tier": "unknown",
        "ops_hub_tier": "unknown",
    }
    results = run_extended_detection(hs, profile)
    print(json.dumps(results, indent=2, default=str))
