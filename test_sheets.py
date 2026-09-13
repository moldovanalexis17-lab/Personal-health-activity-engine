import json
import re
import time
from pathlib import Path

import gspread
import requests
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials

import test_api
from config import (
    CREDENTIALS_FILE,
    SPREADSHEET_ID,
    WORKSHEET_NAME,
    validate_configuration,
)


# ============================================================
# CONFIGURARE
# ============================================================

CACHE_FILE = Path(__file__).with_name(
    "surse_cache.json"
)

INTERVAL_VERIFICARE = 5
MAX_SHEETS_RETRIES = 3
RETRY_DELAY_SECONDS = 3


# ============================================================
# LIMITE INPUT
# ============================================================

VALIDARI = {

    "varsta": {
        "min": 0,
        "max": 90,
    },

    "greutate": {
        "min": 15,
        "max": 180,
    },

    "inaltime": {
        "min": 100,
        "max": 220,
    },

    "apa": {
        "min": 0,
        "max": 6,
    },

    "pasi": {
        "min": 0,
        "max": 100000,
    },

    "somn": {
        "min": 0,
        "max": 16,
    },

    "zile_active": {
        "min": 0,
        "max": 7,
    },

    "minute_zi": {
        "min": 0,
        "max": 600,
    },
}


# ============================================================
# AFISARE TERMINAL
# ============================================================

def titlu(text):

    print()
    print("=" * 60)
    print(text)
    print("=" * 60)


def executa_cu_retry(actiune, operatie):

    ultima_eroare = None

    for incercare in range(
        1,
        MAX_SHEETS_RETRIES + 1,
    ):

        try:
            return actiune()

        except requests.RequestException as eroare:
            ultima_eroare = eroare

            if incercare == MAX_SHEETS_RETRIES:
                break

            print(
                f"{operatie} timed out. Retrying "
                f"({incercare}/{MAX_SHEETS_RETRIES})..."
            )

            time.sleep(
                RETRY_DELAY_SECONDS
            )

    raise ultima_eroare


# ============================================================
# GOOGLE SHEETS - CONECTARE
# ============================================================

def conectare_google_sheets():

    validate_configuration()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_file(
        str(CREDENTIALS_FILE),
        scopes=scopes,
    )

    client = gspread.authorize(
        credentials
    )

    spreadsheet = executa_cu_retry(
        lambda: client.open_by_key(
            SPREADSHEET_ID
        ),
        "Opening Google Spreadsheet",
    )

    worksheet = executa_cu_retry(
        lambda: spreadsheet.worksheet(
            WORKSHEET_NAME
        ),
        "Opening worksheet",
    )

    titlu(
        "GOOGLE SHEETS - CONECTARE"
    )

    print(
        "Spreadsheet:",
        spreadsheet.title
    )

    print(
        "Worksheet:",
        worksheet.title
    )

    return worksheet


# ============================================================
# STRUCTURA INPUT
# ============================================================

def asigura_structura_input(ws):

    titlu(
        "STRUCTURA INPUT"
    )

    executa_cu_retry(
        lambda: ws.update(
            range_name="A1:A4",
            values=[
                ["Age"],
                ["Weight (kg)"],
                ["Height (cm)"],
                ["Activity intensity"],
            ],
        ),
        "Updating profile labels",
    )

    executa_cu_retry(
        lambda: ws.update(
            range_name="D1:D5",
            values=[
                ["Water intake / day (L)"],
                ["Steps / day"],
                ["Sleep hours / night"],
                ["Active days / week"],
                ["Activity minutes / day"],
            ],
        ),
        "Updating activity labels",
    )

    executa_cu_retry(
        lambda: ws.batch_clear([
            "D6:E6"
        ]),
        "Clearing unused input cells",
    )

    print(
        "Input structure checked."
    )


# ============================================================
# VALIDARI GOOGLE SHEETS
# ============================================================

def aplica_validari_google_sheets(ws):

    titlu(
        "VALIDARI GOOGLE SHEETS"
    )

    sheet_id = ws.id

    cereri = [

        # VARSTA
        {
            "setDataValidation": {

                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 1,
                    "endColumnIndex": 2,
                },

                "rule": {

                    "condition": {
                        "type": "NUMBER_BETWEEN",

                        "values": [
                            {
                                "userEnteredValue": "0"
                            },
                            {
                                "userEnteredValue": "90"
                            },
                        ],
                    },

                    "strict": True,

                    "inputMessage":
                        "Allowed age: 0-90 years.",
                },
            }
        },


        # GREUTATE
        {
            "setDataValidation": {

                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 1,
                    "endRowIndex": 2,
                    "startColumnIndex": 1,
                    "endColumnIndex": 2,
                },

                "rule": {

                    "condition": {
                        "type": "NUMBER_BETWEEN",

                        "values": [
                            {
                                "userEnteredValue": "15"
                            },
                            {
                                "userEnteredValue": "180"
                            },
                        ],
                    },

                    "strict": True,

                    "inputMessage":
                        "Allowed weight: 15-180 kg.",
                },
            }
        },


        # INALTIME
        {
            "setDataValidation": {

                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 2,
                    "endRowIndex": 3,
                    "startColumnIndex": 1,
                    "endColumnIndex": 2,
                },

                "rule": {

                    "condition": {
                        "type": "NUMBER_BETWEEN",

                        "values": [
                            {
                                "userEnteredValue": "100"
                            },
                            {
                                "userEnteredValue": "220"
                            },
                        ],
                    },

                    "strict": True,

                    "inputMessage":
                        "Allowed height: 100-220 cm.",
                },
            }
        },


        # INTENSITATE - DROPDOWN
        {
            "setDataValidation": {

                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 3,
                    "endRowIndex": 4,
                    "startColumnIndex": 1,
                    "endColumnIndex": 2,
                },

                "rule": {

                    "condition": {
                        "type": "ONE_OF_LIST",

                        "values": [
                            {
                                "userEnteredValue":
                                    "Moderate"
                            },
                            {
                                "userEnteredValue":
                                    "Vigorous"
                            },
                            {
                                "userEnteredValue":
                                    "Moderata"
                            },
                            {
                                "userEnteredValue":
                                    "Viguros"
                            },
                            {
                                "userEnteredValue":
                                    "Viguroasa"
                            },
                        ],
                    },

                    "showCustomUi": True,

                    "strict": True,

                    "inputMessage":
                        "Select Moderate / Moderata or Vigorous / Viguros.",
                },
            }
        },


        # APA
        {
            "setDataValidation": {

                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                },

                "rule": {

                    "condition": {
                        "type": "NUMBER_BETWEEN",

                        "values": [
                            {
                                "userEnteredValue": "0"
                            },
                            {
                                "userEnteredValue": "6"
                            },
                        ],
                    },

                    "strict": True,

                    "inputMessage":
                        "Allowed water intake: 0-6 L/day.",
                },
            }
        },


        # PASI
        {
            "setDataValidation": {

                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 1,
                    "endRowIndex": 2,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                },

                "rule": {

                    "condition": {
                        "type": "NUMBER_BETWEEN",

                        "values": [
                            {
                                "userEnteredValue": "0"
                            },
                            {
                                "userEnteredValue": "100000"
                            },
                        ],
                    },

                    "strict": True,

                    "inputMessage":
                        "Allowed steps: 0-100000.",
                },
            }
        },


        # SOMN
        {
            "setDataValidation": {

                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 2,
                    "endRowIndex": 3,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                },

                "rule": {

                    "condition": {
                        "type": "NUMBER_BETWEEN",

                        "values": [
                            {
                                "userEnteredValue": "0"
                            },
                            {
                                "userEnteredValue": "16"
                            },
                        ],
                    },

                    "strict": True,

                    "inputMessage":
                        "Allowed sleep: 0-16 hours.",
                },
            }
        },


        # ZILE ACTIVE
        {
            "setDataValidation": {

                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 3,
                    "endRowIndex": 4,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                },

                "rule": {

                    "condition": {
                        "type": "NUMBER_BETWEEN",

                        "values": [
                            {
                                "userEnteredValue": "0"
                            },
                            {
                                "userEnteredValue": "7"
                            },
                        ],
                    },

                    "strict": True,

                    "inputMessage":
                        "Allowed active days: 0-7.",
                },
            }
        },


        # MINUTE ACTIVITATE
        {
            "setDataValidation": {

                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 4,
                    "endRowIndex": 5,
                    "startColumnIndex": 4,
                    "endColumnIndex": 5,
                },

                "rule": {

                    "condition": {
                        "type": "NUMBER_BETWEEN",

                        "values": [
                            {
                                "userEnteredValue": "0"
                            },
                            {
                                "userEnteredValue": "600"
                            },
                        ],
                    },

                    "strict": True,

                    "inputMessage":
                        "Allowed activity minutes: 0-600.",
                },
            }
        },
    ]

    executa_cu_retry(
        lambda: ws.spreadsheet.batch_update(
            {
                "requests": cereri
            }
        ),
        "Applying Google Sheets validation rules",
    )

    print(
        "Google Sheets validation rules applied."
    )


# ============================================================
# CONVERSIE NUMERE
# ============================================================

def numar(valoare):

    if isinstance(
        valoare,
        (int, float)
    ):

        return float(
            valoare
        )

    text = str(
        valoare
    ).strip()

    text = text.replace(
        ",",
        "."
    )

    return float(
        text
    )


# ============================================================
# CITIRE SIGURA CELULA
# ============================================================

def citeste_celula(
    lista,
    index,
    nume,
):

    if index >= len(
        lista
    ):

        raise ValueError(
            f"Lipseste valoarea pentru {nume}."
        )

    rand = lista[
        index
    ]

    if not rand:

        raise ValueError(
            f"Lipseste valoarea pentru {nume}."
        )

    valoare = rand[
        0
    ]

    if valoare is None:

        raise ValueError(
            f"Lipseste valoarea pentru {nume}."
        )

    if str(
        valoare
    ).strip() == "":

        raise ValueError(
            f"Lipseste valoarea pentru {nume}."
        )

    return valoare


# ============================================================
# CITIRE INPUTURI
# ============================================================

def citeste_inputuri(ws):

    rezultate = ws.batch_get([
        "B1:B4",
        "E1:E5",
    ])

    valori_b = rezultate[
        0
    ]

    valori_e = rezultate[
        1
    ]

    date = {

        "varsta": numar(
            citeste_celula(
                valori_b,
                0,
                "Age",
            )
        ),

        "greutate": numar(
            citeste_celula(
                valori_b,
                1,
                "Weight",
            )
        ),

        "inaltime": numar(
            citeste_celula(
                valori_b,
                2,
                "Height",
            )
        ),

        "intensitate": str(
            citeste_celula(
                valori_b,
                3,
                "Activity intensity",
            )
        ).strip(),

        "apa": numar(
            citeste_celula(
                valori_e,
                0,
                "Water intake",
            )
        ),

        "pasi": numar(
            citeste_celula(
                valori_e,
                1,
                "Steps",
            )
        ),

        "somn": numar(
            citeste_celula(
                valori_e,
                2,
                "Sleep",
            )
        ),

        "zile_active": numar(
            citeste_celula(
                valori_e,
                3,
                "Active days",
            )
        ),

        "minute_zi": numar(
            citeste_celula(
                valori_e,
                4,
                "Activity minutes",
            )
        ),
    }

    valideaza_inputuri(
        date
    )

    return date


# ============================================================
# VALIDARE PYTHON
# ============================================================

def valideaza_inputuri(date):

    if (
        date["varsta"]
        != int(date["varsta"])
    ):

        raise ValueError(
            "Age must be a whole number."
        )

    if not (
        0
        <= date["varsta"]
        <= 90
    ):

        raise ValueError(
            "Age must be between 0 and 90."
        )


    if not (
        15
        <= date["greutate"]
        <= 180
    ):

        raise ValueError(
            "Weight must be between 15 and 180 kg."
        )


    if not (
        100
        <= date["inaltime"]
        <= 220
    ):

        raise ValueError(
            "Height must be between 100 and 220 cm."
        )


    intensitate = intensitate_normalizata(
        date["intensitate"]
    )

    if intensitate not in [
        "moderate",
        "vigorous",
    ]:

        raise ValueError(
            "Activity intensity must be Moderate or Vigorous."
        )


    if not (
        0
        <= date["apa"]
        <= 6
    ):

        raise ValueError(
            "Water intake must be between 0 and 6 L/day."
        )


    if (
        date["pasi"]
        != int(date["pasi"])
    ):

        raise ValueError(
            "Steps must be a whole number."
        )

    if not (
        0
        <= date["pasi"]
        <= 100000
    ):

        raise ValueError(
            "Steps must be between 0 and 100000."
        )


    if not (
        0
        <= date["somn"]
        <= 16
    ):

        raise ValueError(
            "Sleep must be between 0 and 16 hours."
        )


    if (
        date["zile_active"]
        != int(date["zile_active"])
    ):

        raise ValueError(
            "Active days must be a whole number."
        )

    if not (
        0
        <= date["zile_active"]
        <= 7
    ):

        raise ValueError(
            "Active days must be between 0 and 7."
        )


    if (
        date["minute_zi"]
        != int(date["minute_zi"])
    ):

        raise ValueError(
            "Activity minutes must be a whole number."
        )

    if not (
        0
        <= date["minute_zi"]
        <= 600
    ):

        raise ValueError(
            "Activity minutes must be between 0 and 600."
        )


# ============================================================
# NORMALIZARE INTENSITATE
# ============================================================

def intensitate_normalizata(text):

    valoare = (
        text
        .strip()
        .lower()
    )

    traduceri = {
        "moderata": "moderate",
        "moderate": "moderate",
        "viguros": "vigorous",
        "viguroasa": "vigorous",
        "vigorous": "vigorous",
    }

    return traduceri.get(
        valoare,
        valoare,
    )


# ============================================================
# DESCARCARE TEXT WEB
# ============================================================

def descarca_text(url):

    headers = {

        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/152 Safari/537.36"
        )
    }

    raspuns = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    raspuns.raise_for_status()

    soup = BeautifulSoup(
        raspuns.text,
        "html.parser",
    )

    return soup.get_text(
        " ",
        strip=True,
    )


# ============================================================
# SOMN LIVE
# ============================================================

def obtine_somn_live():

    titlu(
        "SLEEP - NIH / NHLBI"
    )

    url = (
        "https://www.nhlbi.nih.gov/"
        "health/sleep/how-much-sleep"
    )

    text = descarca_text(
        url
    )

    pattern = re.search(
        r"adults?\s+sleep\s+between\s+"
        r"(\d+(?:\.\d+)?)\s+and\s+"
        r"(\d+(?:\.\d+)?)\s+hours",
        text,
        flags=re.IGNORECASE,
    )

    if not pattern:

        raise RuntimeError(
            "Could not extract the sleep range."
        )

    minim = float(
        pattern.group(1)
    )

    maxim = float(
        pattern.group(2)
    )

    if not (
        5 <= minim <= 12
        and
        5 <= maxim <= 12
        and
        minim <= maxim
    ):

        raise RuntimeError(
            "Invalid sleep range."
        )

    print(
        f"Recommended sleep: "
        f"{minim:g}-{maxim:g} hours/night"
    )

    return {

        "adult_min": minim,

        "adult_max": maxim,

        "sursa": url,

        "status": "ok",
    }


# ============================================================
# APA LIVE
# ============================================================

def obtine_apa_live():

    titlu(
        "HYDRATION - NATIONAL ACADEMIES"
    )

    url = (
        "https://www.nationalacademies.org/"
        "read/10925/chapter/6"
    )

    text = descarca_text(
        url
    )

    pattern = re.search(
        r"19\s*(?:to|through|-)\s*30\s*years"
        r".{0,800}?"
        r"3\.7\s*L"
        r".{0,600}?"
        r"2\.7\s*L",
        text,
        flags=re.IGNORECASE,
    )

    if not pattern:

        raise RuntimeError(
            "Hydration values could not be validated."
        )

    print(
        "Male age 19-30: 3.7 L"
    )

    print(
        "Female age 19-30: 2.7 L"
    )

    return {

        "barbat_19_30": 3.7,

        "femeie_19_30": 2.7,

        "sursa": url,

        "status": "ok",
    }


# ============================================================
# ACTIVITATE - TEST_API
# ============================================================

def obtine_activitate_live():

    rezultat = (
        test_api.test_cdc_activitate()
    )

    if not rezultat:

        raise RuntimeError(
            "CDC nu a returnat date."
        )

    if rezultat.get(
        "status"
    ) != "ok":

        raise RuntimeError(
            "Datele CDC nu sunt valide."
        )

    moderata = rezultat[
        "moderata"
    ]

    viguroasa = rezultat[
        "viguroasa"
    ]

    mod_min = float(
        moderata[
            "min"
        ]
    )

    mod_max = float(
        moderata[
            "max"
        ]
    )

    vig_min = float(
        viguroasa[
            "min"
        ]
    )

    vig_max = float(
        viguroasa[
            "max"
        ]
    )

    return {

        "moderata_min":
            mod_min,

        "moderata_max":
            mod_max,

        "viguroasa_min":
            vig_min,

        "viguroasa_max":
            vig_max,

        "status":
            "ok",
    }


# ============================================================
# PASI - TEST_API
# ============================================================

def obtine_pasi_live():

    iduri = (
        test_api.pubmed_cauta()
    )

    if not iduri:

        raise RuntimeError(
            "PubMed nu a returnat rezultate."
        )

    articol = (
        test_api.pubmed_selecteaza_sursa(
            iduri
        )
    )

    if not articol:

        raise RuntimeError(
            "Nu a fost selectata o sursa PubMed."
        )

    rezultat = (
        test_api.pubmed_extrage_pasi(
            articol
        )
    )

    if not rezultat:

        raise RuntimeError(
            "Nu s-au extras date pentru pasi."
        )

    minim = float(
        rezultat[
            "punct_inflexiune_min"
        ]
    )

    maxim = float(
        rezultat[
            "punct_inflexiune_max"
        ]
    )

    return {

        "min":
            minim,

        "max":
            maxim,

        "status":
            "ok",

        "pmid":
            articol.get("pmid"),

        "doi":
            articol.get("doi"),

        "titlu":
            articol.get("titlu"),
    }


# ============================================================
# CACHE
# ============================================================

def citeste_cache():

    if not CACHE_FILE.exists():

        return {}

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as fisier:

            date = json.load(
                fisier
            )

        if isinstance(
            date,
            dict
        ):

            return date

    except Exception:

        pass

    return {}


def salveaza_cache(surse):

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8",
    ) as fisier:

        json.dump(
            surse,
            fisier,
            indent=4,
            ensure_ascii=False,
        )


# ============================================================
# INCARCARE SURSE
# ============================================================

def incarca_surse():

    titlu(
        "LOADING SOURCES"
    )

    cache = citeste_cache()

    surse = {}

    functii = {

        "activitate":
            obtine_activitate_live,

        "pasi":
            obtine_pasi_live,

        "somn":
            obtine_somn_live,

        "apa":
            obtine_apa_live,
    }

    for nume, functie in functii.items():

        try:

            surse[
                nume
            ] = functie()

            print(
                f"{nume.capitalize()}: LIVE"
            )

        except Exception as eroare:

            print(
                f"{nume.capitalize()} live source failed:",
                eroare
            )

            if nume in cache:

                surse[
                    nume
                ] = cache[
                    nume
                ]

                print(
                    f"{nume.capitalize()}: VALIDATED CACHE"
                )

            else:

                raise RuntimeError(
                    f"No valid data is available for {nume}."
                )

    salveaza_cache(
        surse
    )

    return surse


# ============================================================
# APA RECOMANDATA
# ============================================================

def recomandare_apa(
    varsta,
    sursa,
):

    if 0 <= varsta <= 17:

        return 2.0


    if 18 <= varsta <= 30:

        barbat = float(
            sursa[
                "barbat_19_30"
            ]
        )

        femeie = float(
            sursa[
                "femeie_19_30"
            ]
        )

        return round(
            (
                barbat
                + femeie
            )
            / 2,
            2,
        )


    if 31 <= varsta <= 90:

        return 4.0


    raise ValueError(
        "Invalid age."
    )


# ============================================================
# BMI
# ============================================================

def calculeaza_bmi(
    greutate,
    inaltime_cm,
):

    inaltime_m = (
        inaltime_cm
        / 100
    )

    bmi = (
        greutate
        /
        (
            inaltime_m
            ** 2
        )
    )

    return round(
        bmi,
        1
    )


# ============================================================
# BMI CALIBRAT
# ============================================================

def calculeaza_scor_bmi(
    bmi,
    varsta,
):

    # Pentru persoane sub 20 ani nu folosim
    # clasificarea personalizata de adult.

    if varsta < 20:

        return {

            "scor":
                None,

            "categorie":
                "BMI-for-age required",
        }


    # ========================================================
    # CALIBRARE
    #
    # Repere la 185 cm:
    #
    # < 70 kg      = Subponderal
    # 70 - 75 kg   = Usor subponderal
    # 75 - 85 kg   = Normal
    # 85 - 90 kg   = Usor supraponderal
    # > 90 kg      = Supraponderal
    #
    # Convertite in BMI pentru a functiona proportional
    # si la alte inaltimi.
    # ========================================================

    PRAG_1 = 20.45
    PRAG_2 = 21.91
    PRAG_3 = 24.84
    PRAG_4 = 26.30


    if bmi < PRAG_1:

        return {

            "scor":
                60,

            "categorie":
                "Underweight",
        }


    if bmi < PRAG_2:

        return {

            "scor":
                80,

            "categorie":
                "Slightly underweight",
        }


    if bmi < PRAG_3:

        return {

            "scor":
                100,

            "categorie":
                "Healthy range",
        }


    if bmi < PRAG_4:

        return {

            "scor":
                80,

            "categorie":
                "Slightly above range",
        }


    return {

        "scor":
            60,

        "categorie":
            "Above range",
    }


# ============================================================
# CALCUL ACTIVITATE
# ============================================================

def calculeaza_activitate(
    date,
    sursa,
):

    durata = (
        date[
            "zile_active"
        ]
        *
        date[
            "minute_zi"
        ]
    )

    intensitate = (
        intensitate_normalizata(
            date[
                "intensitate"
            ]
        )
    )


    if intensitate == "moderate":

        minim = float(
            sursa[
                "moderata_min"
            ]
        )

        maxim = float(
            sursa[
                "moderata_max"
            ]
        )


    elif intensitate == "vigorous":

        minim = float(
            sursa[
                "viguroasa_min"
            ]
        )

        maxim = float(
            sursa[
                "viguroasa_max"
            ]
        )


    else:

        raise ValueError(
            "Unknown activity intensity."
        )


    diferenta = max(
        0,
        minim - durata,
    )


    if durata < minim:

        evaluare = (
            f"{diferenta:g} minutes below the minimum"
        )


    elif durata <= maxim:

        evaluare = (
            "Within the recommended range"
        )


    else:

        evaluare = (
            "Above the baseline range"
        )


    return {

        "durata":
            durata,

        "minim":
            minim,

        "maxim":
            maxim,

        "diferenta":
            diferenta,

        "evaluare":
            evaluare,
    }


# ============================================================
# SCOR PROCENT
# ============================================================

def scor_procent(
    valoare,
    tinta,
):

    if tinta <= 0:

        return 0

    scor = round(
        valoare
        /
        tinta
        *
        100
    )

    return max(
        0,
        min(
            100,
            scor
        )
    )


# ============================================================
# SCORURI
# ============================================================

def calculeaza_scoruri(
    date,
    activitate,
    surse,
    apa_recomandata,
):

    scor_activitate = scor_procent(
        activitate[
            "durata"
        ],
        activitate[
            "minim"
        ],
    )


    scor_pasi = scor_procent(
        date[
            "pasi"
        ],
        surse[
            "pasi"
        ][
            "max"
        ],
    )


    scor_somn = scor_procent(
        date[
            "somn"
        ],
        surse[
            "somn"
        ][
            "adult_min"
        ],
    )


    scor_apa = scor_procent(
        date[
            "apa"
        ],
        apa_recomandata,
    )


    return {

        "activitate":
            scor_activitate,

        "pasi":
            scor_pasi,

        "somn":
            scor_somn,

        "hidratare":
            scor_apa,
    }


# ============================================================
# MOTOR PRINCIPAL
# ============================================================

def calculeaza(
    date,
    surse,
):

    activitate = (
        calculeaza_activitate(
            date,
            surse[
                "activitate"
            ],
        )
    )


    apa_recomandata = (
        recomandare_apa(
            date[
                "varsta"
            ],
            surse[
                "apa"
            ],
        )
    )


    bmi = (
        calculeaza_bmi(
            date[
                "greutate"
            ],
            date[
                "inaltime"
            ],
        )
    )


    bmi_rezultat = (
        calculeaza_scor_bmi(
            bmi,
            date[
                "varsta"
            ],
        )
    )


    scoruri = (
        calculeaza_scoruri(
            date,
            activitate,
            surse,
            apa_recomandata,
        )
    )


    scor_bmi = (
        bmi_rezultat[
            "scor"
        ]
    )


    valori_scor = [

        scoruri[
            "activitate"
        ],

        scoruri[
            "pasi"
        ],

        scoruri[
            "somn"
        ],

        scoruri[
            "hidratare"
        ],
    ]


    if scor_bmi is not None:

        valori_scor.append(
            scor_bmi
        )


    scoruri[
        "bmi"
    ] = scor_bmi


    scoruri[
        "total"
    ] = round(
        sum(
            valori_scor
        )
        /
        len(
            valori_scor
        )
    )


    return {

        "activitate":
            activitate,

        "apa_recomandata":
            apa_recomandata,

        "bmi":
            bmi,

        "bmi_scor":
            scor_bmi,

        "bmi_categorie":
            bmi_rezultat[
                "categorie"
            ],

        "scoruri":
            scoruri,
    }


# ============================================================
# SCRIERE REZULTATE
# ============================================================

def scrie_rezultate(
    ws,
    rezultate,
    surse,
):

    activitate = (
        rezultate[
            "activitate"
        ]
    )

    scoruri = (
        rezultate[
            "scoruri"
        ]
    )

    bmi = (
        rezultate[
            "bmi"
        ]
    )

    categorie_bmi = (
        rezultate[
            "bmi_categorie"
        ]
    )

    apa = (
        rezultate[
            "apa_recomandata"
        ]
    )


    somn_min = (
        surse[
            "somn"
        ][
            "adult_min"
        ]
    )

    somn_max = (
        surse[
            "somn"
        ][
            "adult_max"
        ]
    )


    pasi_min = (
        surse[
            "pasi"
        ][
            "min"
        ]
    )

    pasi_max = (
        surse[
            "pasi"
        ][
            "max"
        ]
    )


    # ========================================================
    # G:H - REZULTATE
    # ========================================================

    tabela_rezultate = [

        [
            "Result",
            "Value",
        ],

        [
            "Activity duration (min/week)",
            activitate[
                "durata"
            ],
        ],

        [
            "Minimum target (min/week)",
            activitate[
                "minim"
            ],
        ],

        [
            "Upper target (min/week)",
            activitate[
                "maxim"
            ],
        ],

        [
            "Minutes to minimum target",
            activitate[
                "diferenta"
            ],
        ],

        [
            "Activity assessment",
            activitate[
                "evaluare"
            ],
        ],

        [
            "Recommended sleep (hours/night)",
            (
                f"{somn_min:g}"
                "-"
                f"{somn_max:g}"
            ),
        ],

        [
            "Reference water intake (L/day)",
            apa,
        ],

        [
            "Reference steps (steps/day)",
            (
                f"{pasi_min:g}"
                "-"
                f"{pasi_max:g}"
            ),
        ],

        [
            "BMI",
            bmi,
        ],

        [
            "BMI category",
            categorie_bmi,
        ],
    ]


    # ========================================================
    # J:K - SCORURI
    # ========================================================

    if scoruri[
        "bmi"
    ] is None:

        bmi_scor_afisat = (
            "N/A"
        )

    else:

        bmi_scor_afisat = (
            scoruri[
                "bmi"
            ]
        )


    tabela_scoruri = [

        [
            "Indicator",
            "Score (1-100)",
        ],

        [
            "Activity",
            scoruri[
                "activitate"
            ],
        ],

        [
            "Steps",
            scoruri[
                "pasi"
            ],
        ],

        [
            "Sleep",
            scoruri[
                "somn"
            ],
        ],

        [
            "Hydration",
            scoruri[
                "hidratare"
            ],
        ],

        [
            "BMI",
            bmi_scor_afisat,
        ],

        [
            "Overall score",
            scoruri[
                "total"
            ],
        ],
    ]


    executa_cu_retry(
        lambda: ws.update(
            range_name="G1:H11",
            values=tabela_rezultate,
        ),
        "Writing analysis results",
    )


    executa_cu_retry(
        lambda: ws.update(
            range_name="J1:K7",
            values=tabela_scoruri,
        ),
        "Writing score results",
    )


    executa_cu_retry(
        lambda: ws.batch_clear([
            "G12:H30",
            "J8:K30",
        ]),
        "Clearing unused result cells",
    )


# ============================================================
# SEMNATURA INPUT
# ============================================================

def semnatura_input(date):

    return (

        date[
            "varsta"
        ],

        date[
            "greutate"
        ],

        date[
            "inaltime"
        ],

        intensitate_normalizata(
            date[
                "intensitate"
            ]
        ),

        date[
            "apa"
        ],

        date[
            "pasi"
        ],

        date[
            "somn"
        ],

        date[
            "zile_active"
        ],

        date[
            "minute_zi"
        ],
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("#" * 60)

    print(
        "#     PERSONAL HEALTH & ACTIVITY ENGINE - V1.0"
    )

    print("#" * 60)


    ws = (
        conectare_google_sheets()
    )


    asigura_structura_input(
        ws
    )


    aplica_validari_google_sheets(
        ws
    )


    surse = (
        incarca_surse()
    )


    titlu(
        "ACTIVE MONITORING"
    )

    print(
        "B4: Moderate / Vigorous"
    )

    print(
        "Checking every",
        INTERVAL_VERIFICARE,
        "seconds."
    )

    print(
        "Press Ctrl+C to stop."
    )


    ultima_semnatura = None


    while True:

        try:

            date = (
                citeste_inputuri(
                    ws
                )
            )

            semnatura = (
                semnatura_input(
                    date
                )
            )


            if (
                semnatura
                != ultima_semnatura
            ):

                print()

                print(
                    "Input changed."
                )


                rezultate = (
                    calculeaza(
                        date,
                        surse,
                    )
                )


                scrie_rezultate(
                    ws,
                    rezultate,
                    surse,
                )


                scoruri = (
                    rezultate[
                        "scoruri"
                    ]
                )


                print(
                    "Results updated."
                )


                print(
                    "BMI:",
                    rezultate[
                        "bmi"
                    ]
                )


                print(
                    "BMI category:",
                    rezultate[
                        "bmi_categorie"
                    ]
                )


                if scoruri[
                    "bmi"
                ] is None:

                    print(
                        "BMI score: N/A"
                    )

                else:

                    print(
                        "BMI score:",
                        scoruri[
                            "bmi"
                        ],
                        "/100"
                    )


                print(
                    "Activity:",
                    scoruri[
                        "activitate"
                    ],
                    "/100"
                )


                print(
                    "Steps:",
                    scoruri[
                        "pasi"
                    ],
                    "/100"
                )


                print(
                    "Sleep:",
                    scoruri[
                        "somn"
                    ],
                    "/100"
                )


                print(
                    "Hydration:",
                    scoruri[
                        "hidratare"
                    ],
                    "/100"
                )


                print(
                    "TOTAL:",
                    scoruri[
                        "total"
                    ],
                    "/100"
                )


                ultima_semnatura = (
                    semnatura
                )


        except ValueError as eroare:

            print()

            print(
                    "Waiting for valid input:",
                eroare
            )


        except Exception as eroare:

            print()

            print(
                    "Temporary error:",
                type(
                    eroare
                ).__name__,
                "-",
                eroare
            )


        time.sleep(
            INTERVAL_VERIFICARE
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()
        print()

        print(
            "Program stopped by user."
        )
