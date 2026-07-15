"""
Feature Detection Extensions
============================

Extends HubSpotAuditClient with methods to detect the configuration and usage
of specific HubSpot features documented in references/feature_matrix.md.

Each method returns a FeatureStatus dict:
    {
        "id": str,          # Feature ID from matrix, e.g. "SH-01"
        "name": str,         # Human-readable name
        "in_tier": bool|None,
        "configured": str,   # "yes" | "partial" | "no" | "unknown" | "n/a"
        "actively_used": str, # same values
        "used_well": str,    # same values
        "notes": str,        # Evidence / context
        "weight": str,       # "scored" | "visibility"
        "hub": str,          # "sales" | "marketing" | "service" | etc.
    }

Usage:
    from hs_client import HubSpotAuditClient
    from hs_feature_detect import detect_all_features

    hs = HubSpotAuditClient(token)
    portal_profile = hs.get_portal_profile()  # includes tier info
    features = detect_all_features(hs, portal_profile)

    # Or detect a single hub
    from hs_feature_detect import detect_sales_hub
    sales = detect_sales_hub(hs, portal_profile)
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


def _status(
    feature_id: str,
    name: str,
    hub: str,
    weight: str = "visibility",
    in_tier: Optional[bool] = None,
    configured: str = "unknown",
    actively_used: str = "unknown",
    used_well: str = "unknown",
    notes: str = "",
) -> Dict[str, Any]:
    return {
        "id": feature_id,
        "name": name,
        "hub": hub,
        "weight": weight,
        "in_tier": in_tier,
        "configured": configured,
        "actively_used": actively_used,
        "used_well": used_well,
        "notes": notes,
    }


def _safe(fn, default=None):
    """Run fn; on any exception, return default."""
    try:
        return fn()
    except Exception:
        return default


# =====================================================================
# Sales Hub
# =====================================================================

def detect_sales_hub(hs, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Audit all Sales Hub features documented in the matrix."""
    features: List[Dict[str, Any]] = []

    sales_tier = profile.get("sales_hub_tier", "unknown")  # starter | professional | enterprise | unknown
    in_sales_starter = sales_tier in ("starter", "professional", "enterprise")
    in_sales_pro = sales_tier in ("professional", "enterprise")
    in_sales_enterprise = sales_tier == "enterprise"

    # SH-01: HubSpot Calling
    calling_notes = []
    call_count_30d = 0
    reps_with_calls_30d = 0
    total_sales_reps = 0
    try:
        activity = hs.engagement_activity_by_user(since_days=30)
        reps_with_calls_30d = sum(1 for uid, counts in activity.items() if counts.get("calls", 0) > 0)
        call_count_30d = sum(c.get("calls", 0) for c in activity.values())
        total_sales_reps = len([o for o in hs.list_all_owners() if not o.get("archived", False)])
        calling_notes.append(f"{call_count_30d} calls logged in 30d")
        calling_notes.append(f"{reps_with_calls_30d} of {total_sales_reps} owners logged at least 1 call")
    except Exception as e:
        calling_notes.append(f"check failed: {type(e).__name__}")

    rep_call_pct = (reps_with_calls_30d / total_sales_reps) if total_sales_reps else 0
    call_used_well = (
        "yes" if rep_call_pct >= 0.7 and call_count_30d > 100 else
        "partial" if rep_call_pct >= 0.4 else
        "no"
    )
    features.append(_status(
        "SH-01", "HubSpot Calling (native)", "sales", "scored",
        in_tier=in_sales_starter,
        configured="unknown",  # Would need settings API to confirm number provisioning
        actively_used="yes" if call_count_30d > 10 else "partial" if call_count_30d > 0 else "no",
        used_well=call_used_well,
        notes="; ".join(calling_notes),
    ))

    # SH-02: Dialer integrations
    dialer_present = False
    dialer_name = None
    # Heuristic: check workflow names for dialer references, or installed apps if available
    try:
        wfs = hs.list_all_workflows()
        dialer_keywords = ["aircall", "ringcentral", "kixie", "orum", "five9", "dialpad", "justcall", "phoneburner", "connectandsell"]
        for w in wfs:
            name_low = (w.get("name") or "").lower()
            for kw in dialer_keywords:
                if kw in name_low:
                    dialer_present = True
                    dialer_name = kw
                    break
            if dialer_present:
                break
    except Exception:
        pass
    features.append(_status(
        "SH-02", "Dialer integration (3rd-party)", "sales", "scored",
        in_tier=True,  # Available on any tier via marketplace
        configured="yes" if dialer_present else "no",
        actively_used="unknown",
        used_well="unknown",
        notes=f"Detected: {dialer_name}" if dialer_present else "No third-party dialer detected in workflow names",
    ))

    # SH-03: Deal pipelines and stage design
    try:
        pipes = hs.list_pipelines("deals")
        pipe_count = len(pipes)
        total_stages = sum(len(p.get("stages", [])) for p in pipes)
        pipe_notes = f"{pipe_count} pipeline(s), {total_stages} total stages"
        configured = "yes" if pipe_count > 0 else "no"
        used_well = (
            "yes" if 1 <= pipe_count <= 4 else
            "partial" if pipe_count <= 7 else
            "no"  # sprawl
        )
    except Exception as e:
        pipe_notes = f"error: {type(e).__name__}"
        configured = used_well = "unknown"
    features.append(_status(
        "SH-03", "Deal pipelines and stage design", "sales", "scored",
        in_tier=in_sales_starter,
        configured=configured,
        actively_used="yes" if configured == "yes" else "unknown",
        used_well=used_well,
        notes=pipe_notes,
    ))

    # SH-04: Buying roles
    try:
        br = hs.open_deals_buying_role_coverage(min_deal_amount=1)
        total_open = br.get("total_open_deals_above_threshold", 0)
        with_dm = br.get("deals_with_decision_maker", 0)
        with_any = br.get("deals_with_any_role", 0)
        pct_dm = (with_dm / total_open * 100) if total_open else 0
        br_used_well = (
            "yes" if pct_dm >= 70 else
            "partial" if pct_dm >= 40 else
            "no"
        )
        br_notes = f"{with_dm}/{total_open} open deals have a Decision Maker ({pct_dm:.0f}%); {with_any} have any role"
    except Exception as e:
        br_used_well = "unknown"
        br_notes = f"check failed: {type(e).__name__}"
    features.append(_status(
        "SH-04", "Buying roles on deal-contact associations", "sales", "scored",
        in_tier=in_sales_pro,
        configured="yes" if in_sales_pro else "n/a",
        actively_used="yes" if pct_dm > 10 else "no" if pct_dm == 0 else "partial",
        used_well=br_used_well,
        notes=br_notes,
    ))

    # SH-05: Sequences
    seq_count, seq_enrolled_90d = 0, 0
    try:
        # Sequences don't have a clean v3 endpoint - try /automation/v3/sequences or fallback
        seqs = _safe(lambda: hs._request("GET", "/automation/v3/sequences", note="sequences"), default={})
        if isinstance(seqs, dict) and "results" in seqs:
            seq_count = len(seqs.get("results", []))
    except Exception:
        pass
    features.append(_status(
        "SH-05", "Sequences", "sales", "scored",
        in_tier=in_sales_pro,
        configured="yes" if seq_count > 0 else "no",
        actively_used="unknown",  # Would need enrollment data
        used_well="unknown",
        notes=f"{seq_count} sequences" if seq_count else "No sequences detected via API",
    ))

    # SH-06: Playbooks
    pb_count = 0
    try:
        pbs = _safe(lambda: hs._request("GET", "/crm/v3/objects/playbooks", params={"limit": 100}, note="playbooks"), default={})
        if isinstance(pbs, dict):
            pb_count = len(pbs.get("results", []))
    except Exception:
        pass
    features.append(_status(
        "SH-06", "Playbooks", "sales", "scored",
        in_tier=in_sales_pro,
        configured="yes" if pb_count > 0 else "no",
        actively_used="unknown",
        used_well="unknown",
        notes=f"{pb_count} playbooks" if pb_count else "No playbooks detected",
    ))

    # SH-07: Meeting scheduler / meeting links
    ml_count = 0
    try:
        mls = _safe(lambda: hs._request("GET", "/crm/v3/objects/meetings", params={"limit": 1}, note="meetings count"), default={})
        ml_count = mls.get("total", 0) if isinstance(mls, dict) else 0
    except Exception:
        pass
    # Better: check scheduler pages
    scheduler_notes = f"Meeting object total: {ml_count}"
    features.append(_status(
        "SH-07", "Meeting scheduler / meeting links", "sales", "scored",
        in_tier=in_sales_starter,
        configured="unknown",
        actively_used="yes" if ml_count > 100 else "partial" if ml_count > 0 else "no",
        used_well="unknown",
        notes=scheduler_notes,
    ))

    # SH-08: Forecast tool
    features.append(_status(
        "SH-08", "Forecast tool", "sales", "scored",
        in_tier=in_sales_pro,
        configured="unknown",  # forecast API requires more investigation
        actively_used="unknown",
        used_well="unknown",
        notes="Forecast tool usage not probed by current helper — check manually in portal",
    ))

    # SH-09: Coaching playlists
    features.append(_status(
        "SH-09", "Call coaching / playlists", "sales", "scored",
        in_tier=in_sales_pro,  # playlists require Pro; advanced coaching Enterprise
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Requires calls to coach against — dependent on SH-01/02",
    ))

    # SH-10: Deal priority / score
    try:
        r = hs.property_fill_rate("deals", "hs_priority", sample_size=200)
        pct = (r.get("rate") or 0) * 100
        used_well = "yes" if pct >= 50 else "partial" if pct >= 20 else "no"
        notes = f"hs_priority fill: {pct:.0f}%"
    except Exception as e:
        used_well = "unknown"
        notes = f"check failed: {type(e).__name__}"
    features.append(_status(
        "SH-10", "Deal priority / deal score", "sales", "visibility",
        in_tier=in_sales_pro,
        configured="yes" if "fill:" in notes else "unknown",
        actively_used=used_well,
        used_well=used_well,
        notes=notes,
    ))

    # Visibility features - less exhaustive detection
    features.append(_status("SH-11", "Email templates", "sales", "visibility", in_tier=in_sales_pro, notes="Detection requires templates API"))
    features.append(_status("SH-12", "Snippets", "sales", "visibility", in_tier=True, notes="Detection requires snippets API"))
    features.append(_status("SH-13", "Documents", "sales", "visibility", in_tier=in_sales_pro, notes="Detection requires docs API"))
    features.append(_status("SH-14", "Quotes", "sales", "visibility", in_tier=in_sales_starter, notes="Detection requires quotes endpoint"))
    features.append(_status("SH-15", "Products / line items", "sales", "visibility", in_tier=in_sales_starter, notes="Detection via products API"))
    features.append(_status("SH-18", "Goals", "sales", "visibility", in_tier=in_sales_pro, notes="Detection via goals API"))
    features.append(_status("SH-19", "Prospecting workspace", "sales", "visibility", in_tier=in_sales_pro, notes="Usage detectable via activity patterns"))
    features.append(_status("SH-20", "AI / Sales Intelligence", "sales", "visibility", in_tier=in_sales_pro, notes="Detection via AI feature usage"))

    return features


# =====================================================================
# Marketing Hub
# =====================================================================

def detect_marketing_hub(hs, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    features: List[Dict[str, Any]] = []

    mkt_tier = profile.get("marketing_hub_tier", "unknown")
    in_mkt_starter = mkt_tier in ("starter", "professional", "enterprise")
    in_mkt_pro = mkt_tier in ("professional", "enterprise")
    in_mkt_enterprise = mkt_tier == "enterprise"

    # MH-01: Marketing emails
    features.append(_status(
        "MH-01", "Marketing emails", "marketing", "scored",
        in_tier=in_mkt_starter,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Detection requires marketing email campaigns API",
    ))

    # MH-02: Forms
    try:
        forms = hs.list_all_forms()
        form_count = len(forms)
        features.append(_status(
            "MH-02", "Forms", "marketing", "scored",
            in_tier=True,  # Free feature
            configured="yes" if form_count > 0 else "no",
            actively_used="yes" if form_count > 3 else "partial" if form_count > 0 else "no",
            used_well="yes" if form_count >= 5 else "partial" if form_count > 0 else "no",
            notes=f"{form_count} forms in portal",
        ))
    except Exception as e:
        features.append(_status("MH-02", "Forms", "marketing", "scored",
            in_tier=True, notes=f"detection failed: {type(e).__name__}"))

    # MH-03: Landing pages - requires CMS API
    features.append(_status(
        "MH-03", "Landing pages", "marketing", "scored",
        in_tier=in_mkt_starter,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Detection requires CMS pages API",
    ))

    # MH-04: Workflows (marketing)
    try:
        wfs = hs.list_all_workflows()
        total_wf = len(wfs)
        active_wf = len([w for w in wfs if w.get("enabled")])
        used_well = "yes" if 5 <= active_wf <= 100 else "partial"
        features.append(_status(
            "MH-04", "Workflows", "marketing", "scored",
            in_tier=in_mkt_pro,
            configured="yes" if total_wf > 0 else "no",
            actively_used="yes" if active_wf > 0 else "no",
            used_well=used_well,
            notes=f"{total_wf} workflows ({active_wf} active)",
        ))
    except Exception:
        features.append(_status("MH-04", "Workflows", "marketing", "scored", in_tier=in_mkt_pro))

    # MH-05: Lists
    try:
        lists = hs.list_all_lists()
        list_count = len(lists)
        features.append(_status(
            "MH-05", "Lists", "marketing", "scored",
            in_tier=in_mkt_starter,
            configured="yes" if list_count > 0 else "no",
            actively_used="yes" if list_count > 5 else "partial",
            used_well="yes" if 10 <= list_count <= 150 else "partial" if list_count <= 500 else "no",
            notes=f"{list_count} lists (graveyard risk if >500)",
        ))
    except Exception:
        features.append(_status("MH-05", "Lists", "marketing", "scored", in_tier=in_mkt_starter))

    # MH-06: Campaigns
    campaigns_count = 0
    try:
        c = _safe(lambda: hs._request("GET", "/marketing/v3/campaigns", params={"limit": 100}, note="campaigns"), default={})
        if isinstance(c, dict):
            campaigns_count = len(c.get("results", []))
    except Exception:
        pass
    features.append(_status(
        "MH-06", "Campaigns tool", "marketing", "scored",
        in_tier=in_mkt_pro,
        configured="yes" if campaigns_count > 0 else "no",
        actively_used="yes" if campaigns_count > 3 else "partial" if campaigns_count > 0 else "no",
        used_well="yes" if campaigns_count >= 5 else "partial" if campaigns_count > 0 else "no",
        notes=f"{campaigns_count} campaigns",
    ))

    # MH-07: Attribution reports - hard to detect without reports API
    features.append(_status(
        "MH-07", "Attribution reports", "marketing", "scored",
        in_tier=in_mkt_pro,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Detection requires reports API; check manually",
    ))

    # MH-08: Ad accounts connected
    ads_connected = []
    try:
        ads = _safe(lambda: hs._request("GET", "/marketing/v3/ads/accounts", note="ad accounts"), default={})
        if isinstance(ads, dict):
            ads_connected = ads.get("results", [])
    except Exception:
        pass
    features.append(_status(
        "MH-08", "Ad accounts connected", "marketing", "scored",
        in_tier=in_mkt_pro,
        configured="yes" if ads_connected else "no",
        actively_used="yes" if ads_connected else "no",
        used_well="yes" if len(ads_connected) >= 2 else "partial" if ads_connected else "no",
        notes=f"{len(ads_connected)} ad accounts connected" if ads_connected else "No ad accounts connected",
    ))

    # MH-09: Social accounts
    socials_connected = []
    try:
        socs = _safe(lambda: hs._request("GET", "/marketing/v3/social/accounts", note="social accounts"), default={})
        if isinstance(socs, dict):
            socials_connected = socs.get("results", [])
    except Exception:
        pass
    features.append(_status(
        "MH-09", "Social accounts connected", "marketing", "scored",
        in_tier=in_mkt_pro,
        configured="yes" if socials_connected else "no",
        actively_used="yes" if socials_connected else "no",
        used_well="yes" if len(socials_connected) >= 3 else "partial" if socials_connected else "no",
        notes=f"{len(socials_connected)} social channels connected" if socials_connected else "No social channels",
    ))

    # MH-10: Marketing contacts configuration
    mkt_contacts_count = 0
    try:
        mc = _safe(lambda: hs._request("POST", "/crm/v3/objects/contacts/search",
            json_body={"filterGroups":[{"filters":[{"propertyName":"hs_marketable_status","operator":"EQ","value":"true"}]}],"limit":1},
            note="marketing contacts count"), default={})
        if isinstance(mc, dict):
            mkt_contacts_count = mc.get("total", 0)
    except Exception:
        pass
    features.append(_status(
        "MH-10", "Marketing contacts configuration", "marketing", "scored",
        in_tier=True,  # all tiers
        configured="yes" if mkt_contacts_count > 0 else "unknown",
        actively_used="yes" if mkt_contacts_count > 0 else "unknown",
        used_well="unknown",  # need tier ceiling for true comparison
        notes=f"{mkt_contacts_count} marketing contacts",
    ))

    # Visibility
    features.append(_status("MH-11", "Blog", "marketing", "visibility", in_tier=in_mkt_starter, notes="Requires CMS blog API"))
    features.append(_status("MH-17", "Chat flows", "marketing", "visibility", in_tier=in_mkt_starter))
    features.append(_status("MH-23", "Breeze Content Agent", "marketing", "visibility", in_tier=in_mkt_pro))

    return features


# =====================================================================
# Service Hub
# =====================================================================

def detect_service_hub(hs, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    features: List[Dict[str, Any]] = []

    svc_tier = profile.get("service_hub_tier", "unknown")
    in_svc_free = True  # tickets in free
    in_svc_starter = svc_tier in ("starter", "professional", "enterprise")
    in_svc_pro = svc_tier in ("professional", "enterprise")
    in_svc_enterprise = svc_tier == "enterprise"

    # SVH-01: Tickets and ticket pipelines
    try:
        tickets_total = hs.record_count("tickets")
        pipes = hs.list_pipelines("tickets")
        features.append(_status(
            "SVH-01", "Tickets and ticket pipelines", "service", "scored",
            in_tier=True,
            configured="yes" if pipes else "no",
            actively_used="yes" if tickets_total > 50 else "partial" if tickets_total > 5 else "no",
            used_well="yes" if tickets_total > 50 and len(pipes) >= 1 else "partial" if tickets_total > 0 else "no",
            notes=f"{tickets_total} tickets, {len(pipes)} pipeline(s)",
        ))
    except Exception:
        features.append(_status("SVH-01", "Tickets", "service", "scored", in_tier=True))

    # SVH-02: SLAs
    features.append(_status(
        "SVH-02", "SLAs", "service", "scored",
        in_tier=in_svc_pro,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="SLA detection requires Service API",
    ))

    # SVH-03: Knowledge base
    features.append(_status(
        "SVH-03", "Knowledge base", "service", "scored",
        in_tier=in_svc_pro,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="KB detection requires content API",
    ))

    # SVH-05: Feedback surveys
    features.append(_status(
        "SVH-05", "Feedback surveys (NPS/CSAT/CES)", "service", "scored",
        in_tier=in_svc_starter,  # NPS in starter
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Survey detection requires feedback API",
    ))

    return features


# =====================================================================
# Operations Hub
# =====================================================================

def detect_ops_hub(hs, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    features: List[Dict[str, Any]] = []

    ops_tier = profile.get("ops_hub_tier", "unknown")
    in_ops_starter = ops_tier in ("starter", "professional", "enterprise")
    in_ops_pro = ops_tier in ("professional", "enterprise")
    in_ops_enterprise = ops_tier == "enterprise"

    # OH-01: Data sync
    features.append(_status(
        "OH-01", "Data sync (two-way)", "ops", "scored",
        in_tier=in_ops_starter,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Data sync detection requires integrations API",
    ))

    # OH-02: Data quality automations
    # Heuristic: look for workflow names with "format", "clean", "standardize", "validate"
    dq_keywords = ["format", "clean", "standardize", "validate", "dedupe", "dedup", "lowercase", "uppercase", "hygiene"]
    dq_wf_count = 0
    try:
        wfs = hs.list_all_workflows()
        for w in wfs:
            name_low = (w.get("name") or "").lower()
            if any(kw in name_low for kw in dq_keywords):
                dq_wf_count += 1
    except Exception:
        pass
    features.append(_status(
        "OH-02", "Data quality automations", "ops", "scored",
        in_tier=in_ops_pro,
        configured="yes" if dq_wf_count > 0 else "no",
        actively_used="yes" if dq_wf_count > 0 else "no",
        used_well="yes" if dq_wf_count >= 3 else "partial" if dq_wf_count > 0 else "no",
        notes=f"{dq_wf_count} workflow(s) appear to be data hygiene based on naming",
    ))

    # OH-03: Programmable automation
    # Heuristic: workflows with custom-code actions — we can't see action types without detailed fetch
    features.append(_status(
        "OH-03", "Programmable automation (custom code)", "ops", "scored",
        in_tier=in_ops_pro,
        configured="unknown",
        actively_used="unknown",
        used_well="unknown",
        notes="Custom code action detection requires detailed workflow introspection",
    ))

    return features


# =====================================================================
# Breeze / AI
# =====================================================================

def detect_breeze(hs, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    features: List[Dict[str, Any]] = []

    # BR-01: Copilot (free, detectable via chat assistant properties)
    try:
        contact_props = hs.list_properties("contacts")
        has_chat_props = any("chat_assistant" in (p.get("name") or "") for p in contact_props)
        features.append(_status(
            "BR-01", "Breeze Copilot", "breeze", "scored",
            in_tier=True,
            configured="yes" if has_chat_props else "unknown",
            actively_used="yes" if has_chat_props else "unknown",
            used_well="unknown",
            notes="Chat Assistant properties present" if has_chat_props else "No Chat Assistant indicators",
        ))
    except Exception:
        features.append(_status("BR-01", "Breeze Copilot", "breeze", "scored", in_tier=True))

    # BR-02: Prospecting Agent
    try:
        company_props = hs.list_properties("companies")
        has_prospecting_props = any("prospecting_agent" in (p.get("name") or "") for p in company_props)
        features.append(_status(
            "BR-02", "Breeze Prospecting Agent", "breeze", "scored",
            in_tier=profile.get("sales_hub_tier") in ("professional", "enterprise"),
            configured="yes" if has_prospecting_props else "no",
            actively_used="yes" if has_prospecting_props else "no",
            used_well="unknown",
            notes="Prospecting agent properties present" if has_prospecting_props else "Prospecting agent not in use",
        ))
    except Exception:
        features.append(_status("BR-02", "Breeze Prospecting Agent", "breeze", "scored"))

    # BR-03: Fit Score
    fit_used = False
    try:
        # Check for predictive scoring properties or workflows using fit score
        wfs = hs.list_all_workflows()
        for w in wfs:
            if "fit score" in (w.get("name") or "").lower():
                fit_used = True
                break
    except Exception:
        pass
    features.append(_status(
        "BR-03", "AI Fit Score", "breeze", "scored",
        in_tier=profile.get("marketing_hub_tier") in ("professional", "enterprise"),
        configured="yes" if fit_used else "unknown",
        actively_used="yes" if fit_used else "unknown",
        used_well="unknown",
        notes="Workflow keyed off Fit Score detected" if fit_used else "Fit Score usage not detected in workflows",
    ))

    # BR-04: Engagement Score
    eng_used = False
    try:
        wfs = hs.list_all_workflows() if not fit_used else wfs
        for w in wfs:
            if "engagement score" in (w.get("name") or "").lower():
                eng_used = True
                break
    except Exception:
        pass
    features.append(_status(
        "BR-04", "AI Engagement Score", "breeze", "scored",
        in_tier=profile.get("marketing_hub_tier") in ("professional", "enterprise"),
        configured="yes" if eng_used else "unknown",
        actively_used="yes" if eng_used else "unknown",
        used_well="unknown",
        notes="Workflow keyed off Engagement Score detected" if eng_used else "Engagement Score usage not detected",
    ))

    return features


# =====================================================================
# Orchestrator
# =====================================================================

def detect_all_features(hs, profile: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Run feature detection across all hubs; returns {hub: [features]}."""
    return {
        "sales": detect_sales_hub(hs, profile),
        "marketing": detect_marketing_hub(hs, profile),
        "service": detect_service_hub(hs, profile),
        "ops": detect_ops_hub(hs, profile),
        "breeze": detect_breeze(hs, profile),
    }


def compute_feature_deductions(all_features: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Apply the scoring.md rubric to feature matrix results.

    Returns a dict mapping dimension -> list of deductions:
        {
            "adoption": [{"id": "SH-01", "reason": "...", "amount": -12}, ...],
            ...
        }

    Only "scored" features contribute. "visibility" features never deduct.
    """
    # Mapping of feature ID → (dimension, critical_amount, high_amount)
    # Based on references/scoring.md feature contributions tables
    feature_to_dimension = {
        # Sales Hub → mostly Adoption
        "SH-01": ("adoption", -12, -5),  # Calling
        "SH-02": ("adoption", -12, -5),  # Dialer (alternative to SH-01)
        "SH-03": ("architecture", -8, -3),  # Pipelines
        "SH-04": ("data_health", -12, -5),  # Buying roles (also auto-crit)
        "SH-05": ("adoption", -5, -2),  # Sequences
        "SH-06": ("adoption", -3, -1),  # Playbooks
        "SH-07": ("adoption", -5, -2),  # Meeting scheduler
        "SH-08": ("reporting", -5, -2),  # Forecast
        "SH-09": ("adoption", -5, -2),  # Coaching
        "SH-10": ("adoption", -2, -1),  # Deal priority

        # Marketing
        "MH-01": ("adoption", -3, -1),  # Marketing emails
        "MH-02": ("data_health", -5, -2),  # Forms
        "MH-03": ("adoption", -3, -1),  # Landing pages
        "MH-04": ("automation", -5, -2),  # Workflows
        "MH-05": ("architecture", -3, -1),  # Lists
        "MH-06": ("reporting", -5, -2),  # Campaigns
        "MH-07": ("reporting", -12, -5),  # Attribution
        "MH-08": ("integrations", -5, -2),  # Ad accounts
        "MH-09": ("integrations", -5, -2),  # Social accounts
        "MH-10": ("data_health", -12, -5),  # Marketing contacts bloat

        # Service
        "SVH-01": ("adoption", -3, -1),
        "SVH-02": ("automation", -5, -2),
        "SVH-03": ("adoption", -3, -1),
        "SVH-05": ("reporting", -3, -1),

        # Ops
        "OH-01": ("integrations", -3, -1),
        "OH-02": ("data_health", -5, -2),
        "OH-03": ("automation", -3, -1),

        # Breeze
        "BR-01": ("adoption", -3, -1),
        "BR-02": ("adoption", -3, -1),
        "BR-03": ("reporting", -5, -2),
        "BR-04": ("reporting", -3, -1),
    }

    deductions_by_dim: Dict[str, List[Dict[str, Any]]] = {
        "data_health": [], "architecture": [], "adoption": [],
        "automation": [], "integrations": [], "reporting": [],
    }

    for hub, features in all_features.items():
        for f in features:
            if f.get("weight") != "scored":
                continue
            if not f.get("in_tier"):
                continue  # Can't deduct for a feature the portal doesn't have
            mapping = feature_to_dimension.get(f["id"])
            if not mapping:
                continue
            dimension, crit_amount, high_amount = mapping

            used_well = f.get("used_well", "unknown")
            if used_well == "yes":
                continue  # Nothing to deduct
            elif used_well == "no":
                deductions_by_dim[dimension].append({
                    "source": "feature_matrix",
                    "id": f["id"],
                    "reason": f'{f["name"]} — in-tier but not used',
                    "amount": crit_amount,
                })
            elif used_well == "partial":
                deductions_by_dim[dimension].append({
                    "source": "feature_matrix",
                    "id": f["id"],
                    "reason": f'{f["name"]} — partially used',
                    "amount": high_amount,
                })
            # "unknown" → no deduction (honest uncertainty)

    return deductions_by_dim


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from hs_client import HubSpotAuditClient

    tok = os.environ.get("HUBSPOT_PRIVATE_APP_TOKEN")
    if not tok:
        print("Set HUBSPOT_PRIVATE_APP_TOKEN")
        sys.exit(1)

    hs = HubSpotAuditClient(tok)
    # Minimal profile for testing — would normally come from Phase 1
    profile = {
        "sales_hub_tier": "professional",
        "marketing_hub_tier": "professional",
        "service_hub_tier": "unknown",
        "ops_hub_tier": "unknown",
    }
    all_feats = detect_all_features(hs, profile)
    print(json.dumps(all_feats, indent=2))
    print("\n=== DEDUCTIONS ===")
    print(json.dumps(compute_feature_deductions(all_feats), indent=2))
