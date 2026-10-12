
import io
import math
import re
from collections import defaultdict
from itertools import combinations
from urllib.parse import urlparse

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from rapidfuzz import fuzz


# ==================================================
# APPLICATION CONFIGURATION
# ==================================================

app = FastAPI(
    title="Roll-Up Radar API",
    description=(
        "Company relationship discovery, clustering, "
        "and acquisition analysis."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_COMPANIES = 500
MAX_COLUMNS = 100


# ==================================================
# JSON-SAFE VALUE CONVERSION
# ==================================================

def make_json_safe(value):
    """Convert pandas, NumPy and non-finite values to JSON-safe values."""
    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]

    if value is None:
        return None

    # Handle pandas NA/NaT values.
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    # Convert NumPy scalar values into ordinary Python values.
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass

    if isinstance(value, float) and not math.isfinite(value):
        return None

    return value


# ==================================================
# COLUMN STANDARDIZATION
# ==================================================

FIELD_ALIASES = {
    "company_name": [
        "company_name",
        "company",
        "company name",
        "name",
        "business_name",
        "business name",
    ],
    "website": [
        "website",
        "domain",
        "company_website",
        "company website",
        "url",
    ],
    "phone": [
        "phone",
        "phone_number",
        "phone number",
        "telephone",
    ],
    "address": [
        "address",
        "company_address",
        "company address",
        "street_address",
    ],
    "industry": [
        "industry",
        "sector",
        "category",
    ],
    "employees": [
        "employees",
        "employee_count",
        "employee count",
        "headcount",
        "company_size",
    ],
    "revenue_estimate": [
        "revenue_estimate",
        "revenue",
        "estimated_revenue",
        "annual_revenue",
    ],
}


def clean_text(value):
    """Normalize text and safely handle missing values."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return re.sub(r"\s+", " ", str(value).strip().lower())


def standardize_columns(df):
    """Map common CSV column names to standard field names."""
    df.columns = [
        re.sub(r"\s+", " ", str(column).strip().lower())
        for column in df.columns
    ]

    if any(not column for column in df.columns):
        raise HTTPException(
            status_code=400,
            detail="Every CSV column must have a name.",
        )

    if df.columns.duplicated().any():
        raise HTTPException(
            status_code=400,
            detail="The CSV contains duplicate column names.",
        )

    rename_map = {}

    for standard_name, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in df.columns:
                rename_map[alias] = standard_name
                break

    return df.rename(columns=rename_map)


# ==================================================
# NORMALIZATION HELPERS
# ==================================================

def normalize_domain(value):
    """Extract a normalized website domain."""
    value = clean_text(value)

    if not value:
        return ""

    try:
        parsed = urlparse(
            value if "://" in value else f"https://{value}"
        )
        domain = (parsed.hostname or "").lower().removeprefix("www.")
    except ValueError:
        return ""

    if (
        not domain
        or domain.endswith(".example")
        or domain.endswith(".invalid")
        or domain in {"localhost", "127.0.0.1"}
    ):
        return ""

    return domain


def normalize_phone(value):
    """Normalize phone digits; reject very short identifiers."""
    value = clean_text(value)

    if not value:
        return ""

    digits = re.sub(r"\D", "", value)

    return digits if len(digits) >= 7 else ""



import re

def normalize_address(value):
    """Normalize common address abbreviations and formatting."""
    if value is None:
        return ""

    text = str(value).strip().lower()

    if not text or text in {"nan", "none", "null"}:
        return ""

    # Standardize punctuation and whitespace.
    text = text.replace("&", " and ")
    text = re.sub(r"[.,#]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Normalize common street-type abbreviations.
    replacements = {
        "street": "st",
        "st": "st",
        "road": "rd",
        "rd": "rd",
        "avenue": "ave",
        "av": "ave",
        "ave": "ave",
        "boulevard": "blvd",
        "blvd": "blvd",
        "lane": "ln",
        "ln": "ln",
        "drive": "dr",
        "dr": "dr",
        "way": "way",
        "highway": "hwy",
        "hwy": "hwy",
        "court": "ct",
        "ct": "ct",
        "place": "pl",
        "pl": "pl",
        "suite": "ste",
        "ste": "ste",
    }

    words = text.split()
    words = [replacements.get(word, word) for word in words]

    # Normalize US state names and abbreviations.
    states = {
        "alabama": "al", "alaska": "ak",
        "arizona": "az", "arkansas": "ar",
        "california": "ca", "colorado": "co",
        "connecticut": "ct", "delaware": "de",
        "florida": "fl", "georgia": "ga",
        "hawaii": "hi", "idaho": "id",
        "illinois": "il", "indiana": "in",
        "iowa": "ia", "kansas": "ks",
        "kentucky": "ky", "louisiana": "la",
        "maine": "me", "maryland": "md",
        "massachusetts": "ma", "michigan": "mi",
        "minnesota": "mn", "mississippi": "ms",
        "missouri": "mo", "montana": "mt",
        "nebraska": "ne", "nevada": "nv",
        "new hampshire": "nh", "new jersey": "nj",
        "new mexico": "nm", "new york": "ny",
        "north carolina": "nc", "north dakota": "nd",
        "ohio": "oh", "oklahoma": "ok",
        "oregon": "or", "pennsylvania": "pa",
        "rhode island": "ri", "south carolina": "sc",
        "south dakota": "sd", "tennessee": "tn",
        "texas": "tx", "utah": "ut",
        "vermont": "vt", "virginia": "va",
        "washington": "wa", "west virginia": "wv",
        "wisconsin": "wi", "wyoming": "wy",
    }

    normalized = " ".join(words)

    # Replace full state names, including multi-word names.
    for full_name in sorted(states, key=len, reverse=True):
        normalized = re.sub(
            rf"\b{re.escape(full_name)}\b",
            states[full_name],
            normalized,
        )

    return re.sub(r"\s+", " ", normalized).strip()


import re

def normalize_name(value):
    """Normalize company names for candidate relationship matching."""
    if value is None:
        return ""

    name = str(value).strip().lower()

    if not name or name in {"nan", "none", "null"}:
        return ""

    # Standardize '&' and punctuation.
    name = name.replace("&", " and ")
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()

    # Remove common legal suffixes from the end of the name.
    suffixes = {
        "llc", "inc", "incorporated", "ltd", "limited",
        "corp", "corporation", "co", "company", "plc",
    }

    words = name.split()

    while words and words[-1] in suffixes:
        words.pop()

    return " ".join(words)


def parse_number(value):
    """Parse non-negative numbers and simple currency abbreviations."""
    if value is None:
        return None

    text = clean_text(value)

    if not text:
        return None

    text = text.replace(",", "")
    text = re.sub(r"[$₹£€\s]", "", text)

    multiplier = 1

    if text.endswith("k"):
        multiplier = 1_000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("b"):
        multiplier = 1_000_000_000
        text = text[:-1]

    try:
        number = float(text) * multiplier

        if not math.isfinite(number) or number < 0:
            return None

        return number
    except (ValueError, OverflowError):
        return None


# ==================================================
# CSV VALIDATION
# ==================================================

async def read_company_csv(file: UploadFile):
    """Read a CSV file and validate its basic structure."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The maximum CSV file size is 5 MB.",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded CSV is empty.",
        )

    try:
        csv_text = content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(csv_text))
    except (
        UnicodeDecodeError,
        pd.errors.ParserError,
        ValueError,
    ):
        raise HTTPException(
            status_code=400,
            detail="Could not parse CSV. Check its format and encoding.",
        )

    if len(df.columns) > MAX_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum allowed columns: {MAX_COLUMNS}.",
        )

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="The CSV contains no company records.",
        )

    df = standardize_columns(df)

    if "company_name" not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=(
                "A company name column is required. "
                "Accepted examples: company_name, company, name."
            ),
        )

    # Convert missing values to actual Python None values.
    # The JSON-safe conversion below provides a second safeguard.
    df = df.astype(object).where(pd.notna(df), None)

    records = df.to_dict(orient="records")

    if len(records) > MAX_COMPANIES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum allowed company records: {MAX_COMPANIES}.",
        )

    for row_id, record in enumerate(records):
        record["_row_id"] = row_id

    return df, records


# ==================================================
# ENTITY RESOLUTION
# ==================================================


def find_company_relationships(records):
    """
    Identify potential company relationships using matching evidence.

    A match is a candidate relationship, not proof of common ownership.
    """
    relationships = []

    for first, second in combinations(records, 2):
        evidence = []
        strength = 0

        # 1. Match normalized website domains.
        domain_a = normalize_domain(first.get("website"))
        domain_b = normalize_domain(second.get("website"))

        if domain_a and domain_a == domain_b:
            evidence.append({
                "field": "website",
                "reason": "Exact normalized website domain match",
                "value": domain_a,
            })
            strength += 60

        # 2. Match normalized phone numbers.
        phone_a = normalize_phone(first.get("phone"))
        phone_b = normalize_phone(second.get("phone"))

        if phone_a and phone_a == phone_b:
            evidence.append({
                "field": "phone",
                "reason": "Exact normalized phone match",
                "value": phone_a,
            })
            strength += 50

        # 3. Match normalized addresses.
        address_a = normalize_address(first.get("address"))
        address_b = normalize_address(second.get("address"))

        if address_a and address_a == address_b:
            evidence.append({
                "field": "address",
                "reason": "Exact normalized address match",
                "value": address_a,
            })
            strength += 35

        # 4. Compare normalized company names.
        name_a = normalize_name(first.get("company_name"))
        name_b = normalize_name(second.get("company_name"))

        if name_a and name_b:
            similarity = fuzz.ratio(name_a, name_b)

            if similarity >= 90:
                evidence.append({
                    "field": "company_name",
                    "reason": "Very similar normalized company names",
                    "similarity_percent": round(similarity, 1),
                })
                strength += 25

        # Record the pair only when matching evidence exists.
        if evidence:
            relationships.append({
                "company_a_id": first["_row_id"],
                "company_b_id": second["_row_id"],
                "company_a": first.get("company_name"),
                "company_b": second.get("company_name"),
                "evidence": evidence,
                "evidence_strength": min(strength, 100),
                "relationship_status": "candidate_match",
                "ownership_confirmed": False,
            })

    return relationships

# ==================================================
# RELATIONSHIP CLUSTERING
# ==================================================

def build_clusters(records, relationships):
    """Group connected companies into candidate relationship clusters."""
    parent = {
        record["_row_id"]: record["_row_id"]
        for record in records
    }

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]

        return node

    def union(first, second):
        root_a = find(first)
        root_b = find(second)

        if root_a != root_b:
            parent[root_b] = root_a

    for relationship in relationships:
        union(
            relationship["company_a_id"],
            relationship["company_b_id"],
        )

    groups = defaultdict(list)

    for record in records:
        groups[find(record["_row_id"])].append(record)

    sorted_groups = sorted(
        groups.items(),
        key=lambda item: (
            -len(item[1]),
            str(item[1][0].get("company_name") or ""),
        ),
    )

    clusters = []
    cluster_by_row = {}

    for number, (_, members) in enumerate(sorted_groups, start=1):
        cluster_id = f"CL-{number:03d}"

        for member in members:
            cluster_by_row[member["_row_id"]] = cluster_id

        clusters.append({
            "cluster_id": cluster_id,
            "company_count": len(members),
            "companies": [
                {
                    "company_id": member["_row_id"],
                    "company_name": member.get("company_name"),
                }
                for member in members
            ],
            "status": (
                "candidate_relationship_cluster"
                if len(members) > 1
                else "unlinked_company"
            ),
            "ownership_confirmed": False,
        })

    return clusters, cluster_by_row


# ==================================================
# EXPLAINABLE ACQUISITION-READINESS SCORE
# ==================================================

def score_companies(records):
    """
    Score data completeness, not seller intent or investment quality.
    """
    results = []

    for record in records:
        score = 0
        evidence = []
        missing_fields = []

        industry = clean_text(record.get("industry"))
        employees = parse_number(record.get("employees"))
        revenue = parse_number(record.get("revenue_estimate"))
        website = normalize_domain(record.get("website"))

        if industry:
            score += 20
            evidence.append({
                "field": "industry",
                "contribution": 20,
                "reason": "Industry information is available.",
            })
        else:
            missing_fields.append("industry")

        if employees is not None:
            score += 20
            evidence.append({
                "field": "employees",
                "contribution": 20,
                "reason": "Employee-count information is available.",
                "value": employees,
            })
        else:
            missing_fields.append("employees")

        if revenue is not None:
            score += 25
            evidence.append({
                "field": "revenue_estimate",
                "contribution": 25,
                "reason": "Revenue estimate is available.",
                "value": revenue,
            })
        else:
            missing_fields.append("revenue_estimate")

        if website:
            score += 15
            evidence.append({
                "field": "website",
                "contribution": 15,
                "reason": "A non-placeholder website is available.",
                "value": website,
            })
        else:
            missing_fields.append("website")

        has_contact = bool(
            normalize_phone(record.get("phone"))
            or normalize_address(record.get("address"))
        )

        if has_contact:
            score += 20
            evidence.append({
                "field": "phone/address",
                "contribution": 20,
                "reason": "A phone number or address is available.",
            })
        else:
            missing_fields.append("phone_or_address")

        results.append({
            "company_id": record["_row_id"],
            "company_name": record.get("company_name"),
            "acquisition_readiness_score": score,
            "score_label": (
                "High data completeness"
                if score >= 80
                else "Moderate data completeness"
                if score >= 50
                else "Low data completeness"
            ),
            "score_type": "data_completeness_heuristic",
            "evidence": evidence,
            "missing_fields": missing_fields,
            "seller_intent_predicted": False,
            "limitations": (
                "This score measures data completeness only. "
                "It does not predict business quality, seller intent, "
                "or whether a company is a suitable acquisition."
            ),
        })

    return results


# ==================================================
# PLATFORM / ADD-ON RANKING
# ==================================================

def rank_add_ons(records, platform_id):
    """Rank possible add-ons using transparent industry and size rules."""
    platform = next(
        (
            record
            for record in records
            if record["_row_id"] == platform_id
        ),
        None,
    )

    if platform is None:
        raise HTTPException(
            status_code=404,
            detail="Platform company ID was not found.",
        )

    platform_industry = clean_text(platform.get("industry"))
    platform_employees = parse_number(platform.get("employees"))
    platform_revenue = parse_number(platform.get("revenue_estimate"))

    recommendations = []

    for candidate in records:
        if candidate["_row_id"] == platform_id:
            continue

        score = 0
        evidence = []

        candidate_industry = clean_text(candidate.get("industry"))
        candidate_employees = parse_number(candidate.get("employees"))
        candidate_revenue = parse_number(
            candidate.get("revenue_estimate")
        )

        if platform_industry and candidate_industry:
            if platform_industry == candidate_industry:
                score += 60
                evidence.append({
                    "field": "industry",
                    "reason": "Exact industry match",
                })
            else:
                similarity = fuzz.ratio(
                    platform_industry,
                    candidate_industry,
                )

                if similarity >= 80:
                    score += 30
                    evidence.append({
                        "field": "industry",
                        "reason": "Similar industry labels",
                        "similarity_percent": round(similarity, 1),
                    })

        if (
            platform_employees is not None
            and candidate_employees is not None
            and platform_employees > 0
            and candidate_employees <= platform_employees
        ):
            score += 20
            evidence.append({
                "field": "employees",
                "reason": "Candidate employee count fits the size rule.",
            })

        if (
            platform_revenue is not None
            and candidate_revenue is not None
            and platform_revenue > 0
            and candidate_revenue <= platform_revenue
        ):
            score += 20
            evidence.append({
                "field": "revenue_estimate",
                "reason": "Candidate revenue estimate fits the size rule.",
            })

        if evidence:
            recommendations.append({
                "platform_company": platform.get("company_name"),
                "platform_company_id": platform_id,
                "candidate_company": candidate.get("company_name"),
                "candidate_company_id": candidate["_row_id"],
                "add_on_fit_score": score,
                "evidence": evidence,
                "recommendation_type": "heuristic_candidate",
                "ownership_or_deal_confirmed": False,
            })

    return sorted(
        recommendations,
        key=lambda item: (
            -item["add_on_fit_score"],
            str(item["candidate_company"] or ""),
        ),
    )


# ==================================================
# API ENDPOINTS
# ==================================================

@app.get("/")
def home():
    return {
        "message": "Roll-Up Radar API is running",
        "status": "ok",
        "version": "1.1.0",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "rollup-radar-backend",
    }


@app.post("/api/companies/upload")
async def upload_companies(file: UploadFile = File(...)):
    df, records = await read_company_csv(file)

    preview = [
        {
            key: value
            for key, value in record.items()
            if key != "_row_id"
        }
        for record in records[:10]
    ]

    return make_json_safe({
        "message": "CSV uploaded and parsed successfully.",
        "filename": file.filename,
        "total_records": len(records),
        "columns": df.columns.tolist(),
        "preview": preview,
        "supported_standard_fields": list(FIELD_ALIASES.keys()),
    })


@app.post("/api/companies/analyze")
async def analyze_companies(file: UploadFile = File(...)):
    _, records = await read_company_csv(file)

    relationships = find_company_relationships(records)

    clusters, cluster_by_row = build_clusters(
        records,
        relationships,
    )

    scores = score_companies(records)

    score_by_id = {
        item["company_id"]: item
        for item in scores
    }

    companies = []

    for record in records:
        company_id = record["_row_id"]

        companies.append({
            "company_id": company_id,
            "company_name": record.get("company_name"),
            "website": record.get("website"),
            "phone": record.get("phone"),
            "address": record.get("address"),
            "industry": record.get("industry"),
            "employees": record.get("employees"),
            "revenue_estimate": record.get("revenue_estimate"),
            "cluster_id": cluster_by_row[company_id],
            "acquisition_readiness": score_by_id[company_id],
        })

    return make_json_safe({
        "filename": file.filename,
        "total_companies": len(records),
        "candidate_relationships": len(relationships),
        "total_clusters": len(clusters),
        "companies": companies,
        "relationships": relationships,
        "clusters": clusters,
        "acquisition_readiness": scores,
        "limitations": [
            "Relationships are candidate matches, not confirmed ownership.",
            "The readiness score measures data completeness, not seller intent.",
            "Add-on fit is a heuristic, not investment advice.",
            "Only fields present in the uploaded CSV are analyzed.",
        ],
    })


@app.post("/api/companies/{platform_id}/add-ons")
async def get_add_ons(
    platform_id: int,
    file: UploadFile = File(...),
):
    _, records = await read_company_csv(file)

    recommendations = rank_add_ons(records, platform_id)

    return make_json_safe({
        "platform_company_id": platform_id,
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
        "note": (
            "These are heuristic candidates. They do not establish "
            "deal suitability or common ownership."
        ),
    })


@app.post("/api/companies/export")
async def export_companies(file: UploadFile = File(...)):
    """Export analyzed companies as an enriched CSV."""
    _, records = await read_company_csv(file)

    relationships = find_company_relationships(records)
    clusters, cluster_by_row = build_clusters(records, relationships)
    scores = score_companies(records)

    score_by_id = {
        item["company_id"]: item
        for item in scores
    }

    output = []

    for record in records:
        company_id = record["_row_id"]
        score = score_by_id[company_id]

        output.append({
            "company_name": record.get("company_name"),
            "website": record.get("website"),
            "phone": record.get("phone"),
            "address": record.get("address"),
            "industry": record.get("industry"),
            "employees": record.get("employees"),
            "revenue_estimate": record.get("revenue_estimate"),
            "cluster_id": cluster_by_row[company_id],
            "candidate_relationship_count": sum(
                1
                for relationship in relationships
                if company_id in (
                    relationship["company_a_id"],
                    relationship["company_b_id"],
                )
            ),
            "data_completeness_score": score[
                "acquisition_readiness_score"
            ],
            "score_type": score["score_type"],
        })

    output_df = pd.DataFrame(output)
    csv_content = output_df.to_csv(index=False)

    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8-sig")),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                'attachment; filename="rollup_radar_analysis.csv"'
            )
        },
    )
