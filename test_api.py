
import re
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


# ============================================================
# CONFIGURARE GENERALĂ
# ============================================================

TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


# ============================================================
# PARTEA 1 - CDC
# ACTIVITATE FIZICĂ
# ============================================================

CDC_API_BASE = "https://tools.cdc.gov/api/v2"


# ============================================================
# CERERE HTTP GENERALĂ
# ============================================================

def descarca(url, params=None):

    try:

        raspuns = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT
        )

        print()
        print("------------------------------------------------------------")
        print("URL:")
        print(raspuns.url)
        print("Status:", raspuns.status_code)
        print(
            "Content-Type:",
            raspuns.headers.get("Content-Type")
        )

        raspuns.raise_for_status()

        return raspuns

    except requests.RequestException as eroare:

        print()
        print("EROARE:")
        print(eroare)

        return None


# ============================================================
# HTML -> TEXT
# ============================================================

def curata_html(html):

    if not html:
        return ""

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for element in soup([
        "script",
        "style",
        "noscript",
        "svg"
    ]):
        element.decompose()

    text = soup.get_text(
        " ",
        strip=True
    )

    return re.sub(
        r"\s+",
        " ",
        text
    )


# ============================================================
# CDC - IDENTIFICĂ ARTICOLUL
# ============================================================

def cdc_identifica_articol():

    print()
    print("============================================================")
    print("CDC API - ARTICLE DISCOVERY")
    print("============================================================")

    url = (
        f"{CDC_API_BASE}/resources/media"
    )

    params = {
        "name": "Physical Activity",
        "max": 10
    }

    raspuns = descarca(
        url,
        params
    )

    if raspuns is None:
        return None

    try:

        date = raspuns.json()

    except ValueError:

        print(
            "The CDC response is not valid JSON."
        )

        return None

    rezultate = date.get(
        "results",
        []
    )

    print()
    print(
        "Results found:",
        len(rezultate)
    )

    if not rezultate:
        return None

    articol = rezultate[0]

    print()
    print("ID:", articol.get("id"))
    print("Name:", articol.get("name"))

    return articol


# ============================================================
# CDC - CONȚINUT ARTICOL
# ============================================================

def cdc_continut_articol(media_id):

    url = (
        f"{CDC_API_BASE}/resources/media/"
        f"{media_id}/content"
    )

    print()
    print("============================================================")
    print("CDC API - CONTENT")
    print("============================================================")

    raspuns = descarca(
        url
    )

    if raspuns is None:
        return None

    return raspuns.text


# ============================================================
# CDC - GĂSEȘTE SURSA OFICIALĂ
# ============================================================

def cdc_gaseste_sursa(html):

    print()
    print("============================================================")
    print("CDC - OFFICIAL SOURCES")
    print("============================================================")

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    surse = []

    for link in soup.find_all(
        "a",
        href=True
    ):

        text = link.get_text(
            " ",
            strip=True
        )

        url = link["href"].strip()

        if not url.startswith("http"):
            continue

        text_mic = text.lower()
        url_mic = url.lower()

        if (
            "current guidelines" in text_mic
            or
            "physical activity guidelines" in text_mic
            or
            (
                "odphp.health.gov" in url_mic
                and
                "physical-activity-guidelines" in url_mic
            )
        ):

            surse.append({
                "text": text,
                "url": url
            })

    # Eliminăm duplicatele

    unice = []
    vazute = set()

    for sursa in surse:

        if sursa["url"] not in vazute:

            vazute.add(
                sursa["url"]
            )

            unice.append(
                sursa
            )

    for sursa in unice:

        print()
        print(
            "Text:",
            sursa["text"]
        )

        print(
            "URL:",
            sursa["url"]
        )

    # Preferăm Current Guidelines

    for sursa in unice:

        if "current-guidelines" in sursa["url"].lower():

            return sursa

    if unice:
        return unice[0]

    return None


# ============================================================
# CDC - GĂSEȘTE EXECUTIVE SUMMARY
# ============================================================

def cdc_gaseste_executive_summary(html):

    print()
    print("============================================================")
    print("CDC / ODPHP - EXECUTIVE SUMMARY")
    print("============================================================")

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    documente = []

    for link in soup.find_all(
        "a",
        href=True
    ):

        text = link.get_text(
            " ",
            strip=True
        )

        url = link["href"].strip()

        text_mic = text.lower()
        url_mic = url.lower()

        este_executive = (
            "executive summary" in text_mic
            or
            "executive_summary" in url_mic
            or
            "pag_executive" in url_mic
        )

        if este_executive:

            if url.startswith("/"):

                url = (
                    "https://odphp.health.gov"
                    + url
                )

            documente.append({
                "text": text,
                "url": url
            })

    # Eliminăm duplicatele

    unice = []
    vazute = set()

    for document in documente:

        if document["url"] not in vazute:

            vazute.add(
                document["url"]
            )

            unice.append(
                document
            )

    for document in unice:

        print()
        print(
            "Text:",
            document["text"]
        )

        print(
            "URL:",
            document["url"]
        )

    if unice:
        return unice[0]

    print(
        "Executive Summary nu a fost găsit."
    )

    return None


# ============================================================
# CDC - DESCĂRCARE PDF + EXTRAGERE TEXT
# ============================================================

def cdc_extrage_text_pdf(url):

    print()
    print("============================================================")
    print("CDC - PDF")
    print("============================================================")

    raspuns = descarca(
        url
    )

    if raspuns is None:
        return None

    content_type = raspuns.headers.get(
        "Content-Type",
        ""
    ).lower()

    if "pdf" not in content_type:

        print(
            "The source is not a PDF."
        )

        return None

    nume_pdf = "cdc_guidelines.pdf"

    with open(
        nume_pdf,
        "wb"
    ) as fisier:

        fisier.write(
            raspuns.content
        )

    print(
        "PDF saved:",
        nume_pdf
    )

    try:

        from pypdf import PdfReader

        reader = PdfReader(
            nume_pdf
        )

        print(
            "Page count:",
            len(reader.pages)
        )

        text_complet = ""

        for numar_pagina, pagina in enumerate(
            reader.pages,
            start=1
        ):

            text_pagina = pagina.extract_text()

            if text_pagina:

                text_complet += (
                    f"\n\n--- PAGE {numar_pagina} ---\n"
                )

                text_complet += text_pagina

        print(
            "Characters extracted:",
            len(text_complet)
        )

        return text_complet

    except Exception as eroare:

        print()
        print(
            "PDF ERROR:",
            eroare
        )

        return None


# ============================================================
# CDC - EXTRAGE RECOMANDAREA DE ACTIVITATE
# ============================================================

def cdc_extrage_recomandarea(text, sursa_url):

    print()
    print("============================================================")
    print("CDC - ACTIVITY RECOMMENDATION EXTRACTION")
    print("============================================================")

    rezultat = {
        "status": "not_found",
        "moderata": {
            "min": None,
            "max": None,
            "unitate": "minute/saptamana"
        },
        "viguroasa": {
            "min": None,
            "max": None,
            "unitate": "minute/saptamana"
        },
        "sursa": sursa_url,
        "pagina": None,
        "context": None
    }

    if not text:

        print(
            "The PDF text is empty."
        )

        return rezultat

    # --------------------------------------------------------
    # GĂSIM PAGINA / SECȚIUNEA PENTRU ADULȚI
    # --------------------------------------------------------

    inceput = re.search(
        r"Key Guidelines for Adults",
        text,
        flags=re.IGNORECASE
    )

    sfarsit = re.search(
        r"Key Guidelines for Older Adults",
        text,
        flags=re.IGNORECASE
    )

    if not inceput:

        print(
            "The adult section was not found."
        )

        return rezultat

    poz_start = inceput.start()

    if sfarsit:

        poz_end = sfarsit.start()

    else:

        poz_end = min(
            len(text),
            poz_start + 3000
        )

    sectiune = text[
        poz_start:poz_end
    ]

    # --------------------------------------------------------
    # MODERATĂ
    # --------------------------------------------------------

    pattern_moderata = re.search(
        r"(\d+(?:[.,]\d+)?)\s*minutes?"
        r".{0,180}?"
        r"to"
        r".{0,40}?"
        r"(\d+(?:[.,]\d+)?)\s*minutes?"
        r".{0,120}?"
        r"(?:a|per)\s+week"
        r".{0,80}?"
        r"moderate[- ]intensity",

        sectiune,

        flags=re.IGNORECASE
        | re.DOTALL
    )

    if pattern_moderata:

        rezultat["moderata"]["min"] = float(
            pattern_moderata.group(1)
            .replace(",", ".")
        )

        rezultat["moderata"]["max"] = float(
            pattern_moderata.group(2)
            .replace(",", ".")
        )

        rezultat["pagina"] = 4

        rezultat["context"] = sectiune[
            max(
                0,
                pattern_moderata.start() - 150
            ):
            min(
                len(sectiune),
                pattern_moderata.end() + 300
            )
        ]

    # --------------------------------------------------------
    # VIGUROASĂ
    # --------------------------------------------------------

    pattern_viguroasa = re.search(
        r"or\s+"
        r"(\d+(?:[.,]\d+)?)\s*minutes?"
        r".{0,100}?"
        r"to"
        r".{0,30}?"
        r"(\d+(?:[.,]\d+)?)\s*minutes?"
        r".{0,100}?"
        r"vigorous[- ]intensity",

        sectiune,

        flags=re.IGNORECASE
        | re.DOTALL
    )

    if pattern_viguroasa:

        rezultat["viguroasa"]["min"] = float(
            pattern_viguroasa.group(1)
            .replace(",", ".")
        )

        rezultat["viguroasa"]["max"] = float(
            pattern_viguroasa.group(2)
            .replace(",", ".")
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if (
        rezultat["moderata"]["min"] is not None
        and
        rezultat["moderata"]["max"] is not None
        and
        rezultat["viguroasa"]["min"] is not None
        and
        rezultat["viguroasa"]["max"] is not None
    ):

        rezultat["status"] = "ok"

    # --------------------------------------------------------
    # AFIȘARE
    # --------------------------------------------------------

    print()
    print("===== ACTIVITY RESULT =====")

    print(
        "Moderate:",
        rezultat["moderata"]["min"],
        "-",
        rezultat["moderata"]["max"],
        "minutes/week"
    )

    print(
        "Vigorous:",
        rezultat["viguroasa"]["min"],
        "-",
        rezultat["viguroasa"]["max"],
        "minutes/week"
    )

    print(
        "Status:",
        rezultat["status"]
    )

    print(
        "Source:",
        rezultat["sursa"]
    )

    print(
        "Page:",
        rezultat["pagina"]
    )

    return rezultat


# ============================================================
# TEST COMPLET CDC
# ============================================================

def test_cdc_activitate():

    print()
    print()
    print("############################################################")
    print("#                 CDC TEST - ACTIVITY                     #")
    print("############################################################")

    articol = cdc_identifica_articol()

    if not articol:
        return None

    html_cdc = cdc_continut_articol(
        articol["id"]
    )

    if not html_cdc:
        return None

    sursa = cdc_gaseste_sursa(
        html_cdc
    )

    if not sursa:
        return None

    raspuns_guidelines = descarca(
        sursa["url"]
    )

    if raspuns_guidelines is None:
        return None

    document = cdc_gaseste_executive_summary(
        raspuns_guidelines.text
    )

    if not document:
        return None

    text_pdf = cdc_extrage_text_pdf(
        document["url"]
    )

    if not text_pdf:
        return None

    rezultat = cdc_extrage_recomandarea(
        text_pdf,
        document["url"]
    )

    return rezultat


# ============================================================
# PARTEA 2 - PUBMED
# PAȘI
# ============================================================

PUBMED_BASE = (
    "https://eutils.ncbi.nlm.nih.gov/"
    "entrez/eutils"
)


# ============================================================
# PUBMED - CĂUTARE
# ============================================================

def pubmed_cauta():

    print()
    print()
    print("############################################################")
    print("#                 PUBMED TEST - STEPS                     #")
    print("############################################################")

    termen = (
        '"daily steps"[Title/Abstract] AND '
        '"health outcomes"[Title/Abstract] AND '
        '"systematic review"[Title/Abstract] AND '
        '("dose-response"[Title/Abstract] OR '
        '"meta-analysis"[Title/Abstract])'
    )

    url = (
        f"{PUBMED_BASE}/esearch.fcgi"
    )

    params = {
        "db": "pubmed",
        "term": termen,
        "retmode": "json",
        "retmax": 20,
        "sort": "pub date"
    }

    raspuns = descarca(
        url,
        params
    )

    if raspuns is None:
        return []

    try:

        date = raspuns.json()

    except ValueError:

        print(
            "The PubMed response is not valid JSON."
        )

        return []

    iduri = (
        date
        .get("esearchresult", {})
        .get("idlist", [])
    )

    print()
    print(
        "Articles found:",
        len(iduri)
    )

    return iduri


# ============================================================
# PUBMED - CITIRE ARTICOL
# ============================================================

def pubmed_citeste_articol(pubmed_id):

    url = (
        f"{PUBMED_BASE}/efetch.fcgi"
    )

    params = {
        "db": "pubmed",
        "id": pubmed_id,
        "retmode": "xml"
    }

    raspuns = descarca(
        url,
        params
    )

    if raspuns is None:
        return None

    try:

        root = ET.fromstring(
            raspuns.text
        )

    except ET.ParseError as eroare:

        print(
            "EROARE XML:",
            eroare
        )

        return None

    # --------------------------------------------------------
    # TITLU
    # --------------------------------------------------------

    titlu_element = root.find(
        ".//ArticleTitle"
    )

    if titlu_element is not None:

        titlu = "".join(
            titlu_element.itertext()
        ).strip()

    else:

        titlu = ""

    # --------------------------------------------------------
    # ABSTRACT
    # --------------------------------------------------------

    abstract_parts = []

    for element in root.findall(
        ".//Abstract/AbstractText"
    ):

        text = "".join(
            element.itertext()
        ).strip()

        if text:

            abstract_parts.append(
                text
            )

    abstract = " ".join(
        abstract_parts
    )

    # --------------------------------------------------------
    # DOI
    # --------------------------------------------------------

    doi = None

    for article_id in root.findall(
        ".//ArticleId"
    ):

        if (
            article_id.attrib.get(
                "IdType"
            )
            == "doi"
        ):

            doi = (
                article_id.text or ""
            ).strip()

            break

    # --------------------------------------------------------
    # AN
    # --------------------------------------------------------

    an = None

    pub_date = root.find(
        ".//PubDate"
    )

    if pub_date is not None:

        year_element = pub_date.find(
            "Year"
        )

        if year_element is not None:

            an = year_element.text

    return {
        "pmid": pubmed_id,
        "titlu": titlu,
        "abstract": abstract,
        "doi": doi,
        "an": an
    }


# ============================================================
# PUBMED - ALEGEM SURSĂ POTRIVITĂ
# ============================================================

def pubmed_selecteaza_sursa(iduri):

    print()
    print()
    print("============================================================")
    print("PUBMED - SOURCE SELECTION")
    print("============================================================")

    candidati = []

    for pubmed_id in iduri:

        articol = pubmed_citeste_articol(
            pubmed_id
        )

        if not articol:
            continue

        titlu = articol["titlu"].lower()
        abstract = articol["abstract"].lower()

        scor = 0

        # Titlul trebuie să fie despre pași zilnici
        if "daily steps" in titlu:
            scor += 5

        # Ne interesează health outcomes
        if "health outcomes" in titlu:
            scor += 5

        # Sistematic review
        if "systematic review" in titlu:
            scor += 3

        # Meta-analysis / dose-response
        if "meta-analysis" in titlu:
            scor += 3

        if "dose-response" in titlu:
            scor += 3

        # Abstract relevant
        if "steps per day" in abstract:
            scor += 2

        if "health outcomes" in abstract:
            scor += 2

        candidati.append({
            "scor": scor,
            "articol": articol
        })

    if not candidati:

        print(
            "No candidates were found."
        )

        return None

    # Candidatul cu cel mai mare scor
    candidati.sort(
        key=lambda x: x["scor"],
        reverse=True
    )

    print()

    for candidat in candidati[:10]:

        articol = candidat["articol"]

        print(
            "Scor:",
            candidat["scor"],
            "| PMID:",
            articol["pmid"],
            "|",
            articol["titlu"]
        )

    selectat = candidati[0]["articol"]

    print()
    print("===== SELECTED SOURCE =====")

    print(
        "Title:",
        selectat["titlu"]
    )

    print(
        "PMID:",
        selectat["pmid"]
    )

    print(
        "DOI:",
        selectat["doi"]
    )

    print(
        "Year:",
        selectat["an"]
    )

    return selectat


# ============================================================
# PUBMED - EXTRAGERE PAȘI
# ============================================================

def pubmed_extrage_pasi(articol):

    print()
    print()
    print("============================================================")
    print("PUBMED - STEP DATA EXTRACTION")
    print("============================================================")

    abstract = articol["abstract"]

    rezultat = {
        "status": "not_found",
        "tip": "evidence_based_indicator",
        "unitate": "pasi/zi",
        "punct_inflexiune_min": None,
        "punct_inflexiune_max": None,
        "context_inflexiune": None
    }

    if not abstract:

        print(
            "The abstract is empty."
        )

        return rezultat

    # --------------------------------------------------------
    # PUNCTE DE INFLEXIUNE
    # --------------------------------------------------------
    #
    # Căutăm contextul semantic:
    #
    # inflection points
    # around
    # X-Y steps per day
    #
    # Nu punem valorile în cod.
    # --------------------------------------------------------

    pattern_inflexiune = re.search(
        r"inflection points"
        r".{0,150}?"
        r"(?:around|approximately)"
        r"\s*"
        r"(\d[\d,]*)"
        r"\s*(?:-|to)"
        r"\s*"
        r"(\d[\d,]*)"
        r"\s*steps?\s*per\s*day",

        abstract,

        flags=re.IGNORECASE
        | re.DOTALL
    )

    if pattern_inflexiune:

        rezultat[
            "punct_inflexiune_min"
        ] = int(
            pattern_inflexiune.group(1)
            .replace(",", "")
        )

        rezultat[
            "punct_inflexiune_max"
        ] = int(
            pattern_inflexiune.group(2)
            .replace(",", "")
        )

        rezultat[
            "context_inflexiune"
        ] = abstract[
            max(
                0,
                pattern_inflexiune.start() - 150
            ):
            min(
                len(abstract),
                pattern_inflexiune.end() + 300
            )
        ]

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if (
        rezultat["punct_inflexiune_min"]
        is not None
        and
        rezultat["punct_inflexiune_max"]
        is not None
    ):

        rezultat["status"] = "ok"

    # --------------------------------------------------------
    # AFIȘARE
    # --------------------------------------------------------

    print()
    print("===== STEP RESULT =====")

    print(
        "Inflection point:",
        rezultat["punct_inflexiune_min"],
        "-",
        rezultat["punct_inflexiune_max"],
        "steps/day"
    )

    print(
        "Tip:",
        rezultat["tip"]
    )

    print(
        "Status:",
        rezultat["status"]
    )

    print()
    print("===== INFLECTION CONTEXT =====")

    print(
        rezultat["context_inflexiune"]
    )

    return rezultat


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("############################################################")
    print("#              ANALIZOR - SURSE EXTERNE                   #")
    print("############################################################")

    # --------------------------------------------------------
    # CDC - ACTIVITATE
    # --------------------------------------------------------

    rezultat_cdc = test_cdc_activitate()

    # --------------------------------------------------------
    # PUBMED - PAȘI
    # --------------------------------------------------------

    iduri_pubmed = pubmed_cauta()

    rezultat_pasi = None

    if iduri_pubmed:

        articol_pasi = pubmed_selecteaza_sursa(
            iduri_pubmed
        )

        if articol_pasi:

            rezultat_pasi = pubmed_extrage_pasi(
                articol_pasi
            )

    # --------------------------------------------------------
    # REZUMAT
    # --------------------------------------------------------

    print()
    print()
    print("############################################################")
    print("#                    REZUMAT FINAL                        #")
    print("############################################################")

    print()
    print("ACTIVITATE CDC")

    if rezultat_cdc:

        print(
            "Moderată:",
            rezultat_cdc["moderata"]["min"],
            "-",
            rezultat_cdc["moderata"]["max"],
            "minute/săptămână"
        )

        print(
            "Viguroasă:",
            rezultat_cdc["viguroasa"]["min"],
            "-",
            rezultat_cdc["viguroasa"]["max"],
            "minute/săptămână"
        )

        print(
            "Status:",
            rezultat_cdc["status"]
        )

    else:

        print(
            "Datele CDC nu au fost extrase."
        )

    print()
    print("PAȘI PUBMED")

    if rezultat_pasi:

        print(
            "Punct de inflexiune:",
            rezultat_pasi[
                "punct_inflexiune_min"
            ],
            "-",
            rezultat_pasi[
                "punct_inflexiune_max"
            ],
            "pași/zi"
        )

        print(
            "Status:",
            rezultat_pasi["status"]
        )

    else:

        print(
            "Datele PubMed nu au fost extrase."
        )

    print()
    print("############################################################")
    print("#                     TEST TERMINAT                       #")
    print("############################################################")
