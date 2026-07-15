#!/usr/bin/env python3
"""
Verify Astor/Sierra parity — confirms 42/42 contact and 39/39 company ZI properties.
Requires CLIENT_HUBSPOT_TOKEN env var.
"""

import requests, os

TOKEN = os.environ.get("CLIENT_HUBSPOT_TOKEN")
if not TOKEN:
    raise SystemExit("ERROR: CLIENT_HUBSPOT_TOKEN not set.")

HEADERS = {"Authorization": f"Bearer {TOKEN}"}
BASE = "https://api.hubapi.com"

SIERRA_CONTACTS = {
    "management_level","person_linkedin_url","zoominfo___direct_phone_contact_source_yrl",
    "zoominfo___email_contact_source_url","zoominfo___fax","zoominfo___full_contact_address",
    "zoominfo___full_name","zoominfo_company_id","zoominfo_company_profile_url",
    "zoominfo_contact_accuracy_grade_","zoominfo_contact_accuracy_score_","zoominfo_contact_id",
    "zoominfo_contact_profile_url","zoominfo_contact_tag___private","zoominfo_contact_tag___public",
    "zoominfo_contact_within_eu_","zoominfo_department_","zoominfo_direct_phone_number",
    "zoominfo_do_not_call_direct_","zoominfo_do_not_call_mobile_","zoominfo_education_",
    "zoominfo_email_matches_company_name_","zoominfo_employment_history_","zoominfo_enrich_status",
    "zoominfo_job_change_date_","zoominfo_job_change_type_","zoominfo_job_function",
    "zoominfo_last_mentioned","zoominfo_last_updated_date_","zoominfo_management_level",
    "zoominfo_mobile_contact_source_url","zoominfo_mobile_phone","zoominfo_neverbounce_email_status_",
    "zoominfo_person_has_moved","zoominfo_person_looks_like_eu_","zoominfo_previous_company_name_",
    "zoominfo_previous_job_title_","zoominfo_record_purchased_date_","zoominfo_tag",
    "zoominfo_url","zoominfo_workflow_name","zoominfo_zoominfo_url",
}

SIERRA_COMPANIES = {
    "company_zoominfo_url","zoominfo_all_industries","zoominfo_all_investors",
    "zoominfo_all_sub_industries","zoominfo_certification_date","zoominfo_certified_active_company",
    "zoominfo_company_attributes","zoominfo_company_id","zoominfo_company_linkedin_url",
    "zoominfo_company_other_domains","zoominfo_company_tag","zoominfo_company_tag___private",
    "zoominfo_company_tag___public","zoominfo_company_type","zoominfo_domain_rank",
    "zoominfo_employee_range","zoominfo_finance_department_budget","zoominfo_founded_year",
    "zoominfo_full_company_address","zoominfo_funding_rounds","zoominfo_hr_department_budget",
    "zoominfo_it_department_budget","zoominfo_marketing_department_budget","zoominfo_naics_code",
    "zoominfo_number_of_locations","zoominfo_parent_company_name","zoominfo_parent_company_zoominfo_id",
    "zoominfo_past_1_year_employee_growth_rate","zoominfo_past_2_year_employee_growth_rate",
    "zoominfo_primary_industry","zoominfo_primary_sub_industry","zoominfo_products_and_services",
    "zoominfo_ranking","zoominfo_revenue_range","zoominfo_sic_code","zoominfo_technologies",
    "zoominfo_ticker","zoominfo_total_funding","zoominfo_workflow_name",
}

all_pass = True
for obj, target in [("contacts", SIERRA_CONTACTS), ("companies", SIERRA_COMPANIES)]:
    r = requests.get(f"{BASE}/crm/v3/properties/{obj}", headers=HEADERS)
    existing = {p["name"] for p in r.json().get("results", [])}
    matched = target & existing
    missing = target - existing
    status = "✅" if not missing else "❌"
    print(f"{status} {obj.upper()}: {len(matched)}/{len(target)} matched")
    if missing:
        all_pass = False
        for m in sorted(missing):
            print(f"   MISSING: {m}")

print()
if all_pass:
    print("✅ Full parity confirmed — ready for ZoomInfo field mapping.")
else:
    print("❌ Parity gaps found — run deploy.py to fill missing properties.")
