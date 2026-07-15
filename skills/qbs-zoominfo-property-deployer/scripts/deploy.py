#!/usr/bin/env python3
"""
QBS ZoomInfo Property Deployer
Deploys 42 contact + 39 company ZoomInfo enrichment properties into a HubSpot portal.
Requires CLIENT_HUBSPOT_TOKEN env var set to the client PAT.
"""

import requests
import os
import time

TOKEN = os.environ.get("CLIENT_HUBSPOT_TOKEN")
if not TOKEN:
    raise SystemExit("ERROR: CLIENT_HUBSPOT_TOKEN not set. Export the client PAT first.")

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
BASE = "https://api.hubapi.com"

# ── Property definitions ──────────────────────────────────────────────────────

# (internal_name, label, type, fieldType, groupName)
CONTACT_PROPS = [
    # Standard contact group — non-zoominfo group
    ("management_level",                        "Management Level",                         "string",   "text",     "contactinformation"),
    ("person_linkedin_url",                     "Person LinkedIn URL",                      "string",   "text",     "contactinformation"),
    # ZoomInfo group — core ID / profile
    ("zoominfo_contact_id",                     "ZoomInfo Contact ID",                      "string",   "text",     "zoominfo"),
    ("zoominfo_contact_profile_url",            "ZoomInfo Contact Profile URL",             "string",   "text",     "zoominfo"),
    ("zoominfo_company_id",                     "ZoomInfo Company ID",                      "string",   "text",     "zoominfo"),
    ("zoominfo_company_profile_url",            "ZoomInfo Company Profile URL",             "string",   "text",     "zoominfo"),
    ("zoominfo_enrich_status",                  "ZoomInfo Enrich Status",                   "string",   "text",     "zoominfo"),
    ("zoominfo_tag",                            "ZoomInfo Contact Tag",                     "string",   "text",     "zoominfo"),
    ("zoominfo_contact_tag___private",          "ZoomInfo Contact Tag - Private",           "string",   "text",     "zoominfo"),
    ("zoominfo_contact_tag___public",           "ZoomInfo Contact Tag - Public",            "string",   "text",     "zoominfo"),
    ("zoominfo_workflow_name",                  "ZoomInfo Workflow Name",                   "string",   "text",     "zoominfo"),
    ("zoominfo_url",                            "ZoomInfo URL",                             "string",   "text",     "zoominfo"),
    ("zoominfo_zoominfo_url",                   "ZoomInfo ZoomInfo URL",                    "string",   "text",     "zoominfo"),
    # Contact info / phone
    ("zoominfo_direct_phone_number",            "Zoominfo Direct Phone Number",             "string",   "text",     "zoominfo"),
    ("zoominfo_mobile_phone",                   "ZoomInfo Mobile Phone",                    "string",   "text",     "zoominfo"),
    ("zoominfo___fax",                          "ZoomInfo Fax",                             "string",   "text",     "zoominfo"),
    ("zoominfo___full_name",                    "ZoomInfo Full Name",                       "string",   "text",     "zoominfo"),
    ("zoominfo___full_contact_address",         "ZoomInfo Full Contact Address",            "string",   "text",     "zoominfo"),
    # Role / seniority
    ("zoominfo_department_",                    "ZoomInfo Department",                      "string",   "text",     "zoominfo"),
    ("zoominfo_management_level",               "ZoomInfo Management Level",                "string",   "text",     "zoominfo"),
    ("zoominfo_job_function",                   "ZoomInfo Job Function",                    "string",   "text",     "zoominfo"),
    # Accuracy / compliance
    ("zoominfo_contact_accuracy_score_",        "ZoomInfo Contact Accuracy Score",          "number",   "number",   "zoominfo"),
    ("zoominfo_contact_accuracy_grade_",        "ZoomInfo Contact Accuracy Grade",          "string",   "text",     "zoominfo"),
    ("zoominfo_neverbounce_email_status_",      "ZoomInfo NeverBounce Email Status",        "string",   "text",     "zoominfo"),
    ("zoominfo_email_matches_company_name_",    "ZoomInfo Email Matches Company Name",      "string",   "text",     "zoominfo"),
    ("zoominfo_contact_within_eu_",             "ZoomInfo Contact Within EU",               "string",   "text",     "zoominfo"),
    ("zoominfo_person_looks_like_eu_",          "ZoomInfo Person Looks Like EU",            "string",   "text",     "zoominfo"),
    ("zoominfo_do_not_call_direct_",            "ZoomInfo Do Not Call Direct",              "string",   "text",     "zoominfo"),
    ("zoominfo_do_not_call_mobile_",            "ZoomInfo Do Not Call Mobile",              "string",   "text",     "zoominfo"),
    # Source URLs
    ("zoominfo___direct_phone_contact_source_yrl", "ZoomInfo Direct Phone Contact Source YRL", "string", "text",   "zoominfo"),
    ("zoominfo___email_contact_source_url",     "ZoomInfo Email Contact Source URL",        "string",   "text",     "zoominfo"),
    ("zoominfo_mobile_contact_source_url",      "ZoomInfo Mobile Contact Source URL",       "string",   "text",     "zoominfo"),
    # Job change / movement
    ("zoominfo_job_change_date_",               "ZoomInfo Job Change Date",                 "date",     "date",     "zoominfo"),
    ("zoominfo_job_change_type_",               "ZoomInfo Job Change Type",                 "string",   "text",     "zoominfo"),
    ("zoominfo_person_has_moved",               "ZoomInfo Person Has Moved",                "string",   "text",     "zoominfo"),
    ("zoominfo_previous_company_name_",         "ZoomInfo Previous Company Name",           "string",   "text",     "zoominfo"),
    ("zoominfo_previous_job_title_",            "ZoomInfo Previous Job Title",              "string",   "text",     "zoominfo"),
    # History / metadata
    ("zoominfo_last_mentioned",                 "ZoomInfo Last Mentioned",                  "date",     "date",     "zoominfo"),
    ("zoominfo_last_updated_date_",             "ZoomInfo Last Updated Date",               "date",     "date",     "zoominfo"),
    ("zoominfo_record_purchased_date_",         "ZoomInfo Record Purchased Date",           "date",     "date",     "zoominfo"),
    ("zoominfo_employment_history_",            "ZoomInfo Employment History",              "string",   "text",     "zoominfo"),
    ("zoominfo_education_",                     "ZoomInfo Education",                       "string",   "text",     "zoominfo"),
]

COMPANY_PROPS = [
    # Standard company group
    ("company_zoominfo_url",                    "Company ZoomInfo URL",                     "string",   "text",     "companyinformation"),
    # ZoomInfo group — core ID / profile
    ("zoominfo_company_id",                     "ZoomInfo Company ID",                      "string",   "text",     "zoominfo"),
    ("zoominfo_company_linkedin_url",           "ZoomInfo Company LinkedIn URL",            "string",   "text",     "zoominfo"),
    ("zoominfo_full_company_address",           "ZoomInfo Full Company Address",            "string",   "text",     "zoominfo"),
    ("zoominfo_company_other_domains",          "ZoomInfo Company Other Domains",           "string",   "text",     "zoominfo"),
    ("zoominfo_company_attributes",             "ZoomInfo Company Attributes",              "string",   "text",     "zoominfo"),
    ("zoominfo_company_tag",                    "ZoomInfo Company Tag",                     "string",   "text",     "zoominfo"),
    ("zoominfo_company_tag___private",          "ZoomInfo Company Tag - Private",           "string",   "text",     "zoominfo"),
    ("zoominfo_company_tag___public",           "ZoomInfo Company Tag - Public",            "string",   "text",     "zoominfo"),
    ("zoominfo_workflow_name",                  "ZoomInfo Workflow Name",                   "string",   "text",     "zoominfo"),
    # Firmographics
    ("zoominfo_company_type",                   "ZoomInfo Company Type",                    "string",   "text",     "zoominfo"),
    ("zoominfo_founded_year",                   "ZoomInfo Founded Year",                    "string",   "text",     "zoominfo"),
    ("zoominfo_employee_range",                 "ZoomInfo Employee Range",                  "string",   "text",     "zoominfo"),
    ("zoominfo_revenue_range",                  "ZoomInfo Revenue Range",                   "string",   "text",     "zoominfo"),
    ("zoominfo_number_of_locations",            "ZoomInfo Number of Locations",             "number",   "number",   "zoominfo"),
    ("zoominfo_ranking",                        "ZoomInfo Ranking",                         "number",   "number",   "zoominfo"),
    ("zoominfo_domain_rank",                    "ZoomInfo Domain Rank",                     "number",   "number",   "zoominfo"),
    ("zoominfo_ticker",                         "ZoomInfo Ticker",                          "string",   "text",     "zoominfo"),
    # Industry / classification
    ("zoominfo_naics_code",                     "ZoomInfo NAICS Code",                      "string",   "text",     "zoominfo"),
    ("zoominfo_sic_code",                       "ZoomInfo SIC Code",                        "string",   "text",     "zoominfo"),
    ("zoominfo_primary_industry",               "ZoomInfo Primary Industry",                "string",   "text",     "zoominfo"),
    ("zoominfo_primary_sub_industry",           "ZoomInfo Primary Sub-Industry",            "string",   "text",     "zoominfo"),
    ("zoominfo_all_industries",                 "ZoomInfo All Industries",                  "string",   "text",     "zoominfo"),
    ("zoominfo_all_sub_industries",             "ZoomInfo All Sub-Industries",              "string",   "text",     "zoominfo"),
    ("zoominfo_products_and_services",          "ZoomInfo Products and Services",           "string",   "text",     "zoominfo"),
    ("zoominfo_technologies",                   "ZoomInfo Technologies",                    "string",   "text",     "zoominfo"),
    # Active status / certification
    ("zoominfo_certified_active_company",       "ZoomInfo Certified Active Company",        "string",   "text",     "zoominfo"),
    ("zoominfo_certification_date",             "ZoomInfo Certification Date",              "date",     "date",     "zoominfo"),
    # Funding
    ("zoominfo_total_funding",                  "ZoomInfo Total Funding",                   "number",   "number",   "zoominfo"),
    ("zoominfo_funding_rounds",                 "ZoomInfo Funding Rounds",                  "number",   "number",   "zoominfo"),
    ("zoominfo_all_investors",                  "ZoomInfo All Investors",                   "string",   "text",     "zoominfo"),
    # Growth signals
    ("zoominfo_past_1_year_employee_growth_rate",  "ZoomInfo Past 1 Year Employee Growth Rate",  "number", "number", "zoominfo"),
    ("zoominfo_past_2_year_employee_growth_rate",  "ZoomInfo Past 2 Year Employee Growth Rate",  "number", "number", "zoominfo"),
    # Department budgets
    ("zoominfo_it_department_budget",           "ZoomInfo IT Department Budget",            "number",   "number",   "zoominfo"),
    ("zoominfo_marketing_department_budget",    "ZoomInfo Marketing Department Budget",     "number",   "number",   "zoominfo"),
    ("zoominfo_finance_department_budget",      "ZoomInfo Finance Department Budget",       "number",   "number",   "zoominfo"),
    ("zoominfo_hr_department_budget",           "ZoomInfo HR Department Budget",            "number",   "number",   "zoominfo"),
    # Parent company
    ("zoominfo_parent_company_name",            "ZoomInfo Parent Company Name",             "string",   "text",     "zoominfo"),
    ("zoominfo_parent_company_zoominfo_id",     "ZoomInfo Parent Company ZoomInfo ID",      "number",   "number",   "zoominfo"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def ensure_group(obj, name, label):
    r = requests.post(
        f"{BASE}/crm/v3/properties/{obj}/groups",
        headers=HEADERS,
        json={"name": name, "label": label, "displayOrder": 99},
    )
    if r.status_code in (200, 201):
        print(f"  [GROUP OK] {obj}/{name}")
    elif r.status_code == 409:
        pass  # already exists, fine
    else:
        print(f"  [GROUP ERR {r.status_code}] {obj}/{name}: {r.text[:80]}")


def create_prop(obj, name, label, ptype, fieldtype, group):
    r = requests.post(
        f"{BASE}/crm/v3/properties/{obj}",
        headers=HEADERS,
        json={
            "name": name, "label": label, "type": ptype,
            "fieldType": fieldtype, "groupName": group,
            "hasUniqueValue": False, "hidden": False,
        },
    )
    if r.status_code in (200, 201):
        return "OK"
    elif r.status_code == 409:
        return "EXISTS"
    else:
        return f"ERR {r.status_code}: {r.text[:80]}"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Verify token / portal
    r = requests.get(f"{BASE}/account-info/v3/details", headers={"Authorization": f"Bearer {TOKEN}"})
    info = r.json()
    portal_id = info.get("portalId")
    print(f"\n📋 Portal: {portal_id} | DC: {info.get('dataCenter','?')} | Type: {info.get('accountType','?')}")
    print(f"{'─'*60}")

    # Create ZoomInfo property groups
    print("\n🗂  Ensuring property groups...")
    ensure_group("contacts", "zoominfo", "ZoomInfo")
    ensure_group("companies", "zoominfo", "ZoomInfo")

    # Deploy contact properties
    print(f"\n👤 Deploying {len(CONTACT_PROPS)} contact properties...")
    ok = exists = err = 0
    for name, label, ptype, ft, group in CONTACT_PROPS:
        result = create_prop("contacts", name, label, ptype, ft, group)
        if result == "OK":
            ok += 1
        elif result == "EXISTS":
            exists += 1
        else:
            err += 1
            print(f"  [ERR] {name}: {result}")
        time.sleep(0.12)
    print(f"  ✅ Created: {ok} | Already existed: {exists} | Errors: {err}")

    # Deploy company properties
    print(f"\n🏢 Deploying {len(COMPANY_PROPS)} company properties...")
    ok = exists = err = 0
    for name, label, ptype, ft, group in COMPANY_PROPS:
        result = create_prop("companies", name, label, ptype, ft, group)
        if result == "OK":
            ok += 1
        elif result == "EXISTS":
            exists += 1
        else:
            err += 1
            print(f"  [ERR] {name}: {result}")
        time.sleep(0.12)
    print(f"  ✅ Created: {ok} | Already existed: {exists} | Errors: {err}")

    print(f"\n{'─'*60}")
    print(f"✅ Done — {len(CONTACT_PROPS)} contact + {len(COMPANY_PROPS)} company properties deployed.")
    print(f"   Next: configure field mapping in ZoomInfo → Integrations → HubSpot.\n")


if __name__ == "__main__":
    main()
