"""This module contains configuration constants used across the framework"""

from itk_dev_shared_components.kmd_nova.nova_objects import Caseworker, Department

# The number of times the robot retries on an error before terminating.
MAX_RETRY_COUNT = 3

# Whether the robot should be marked as failed if MAX_RETRY_COUNT is reached.
FAIL_ROBOT_ON_TOO_MANY_ERRORS = True

# Error screenshot config
SMTP_SERVER = "smtp.adm.aarhuskommune.dk"
SMTP_PORT = 25
SCREENSHOT_SENDER = "robot@friend.dk"

# Constant/Credential names
ERROR_EMAIL = "Error Email"
NOVA_API = "Nova API"
GRAPH_API = "Graph API"

MAILBOX = "folkeregister@aarhus.dk"
SOURCE_FOLDER = "Selvbetjening UA og UFB"
DONE_FOLDER = "Slettetmappen 6"

VALID_SENDER = "selvbetjening.aarhuskommune.dk"
VALID_SUBJECTS = (
    "Uden fast bopæl i en midlertidig periode (fra Selvbetjening.aarhuskommune.dk)",
    "Webform submission from: Without permanent residence",
)

# KMD Nova case settings.
CASE_TITLE = "Folkeregistrering i almindelighed"
KLE_NUMBER = "23.05.00"
PROCEEDING_FACET = "G01"
CASE_SENSITIVITY = "Følsomme"

RESPONSIBLE_DEPARTMENT = Department(
    id=70403,
    name="Folkeregister og Sygesikring",
    user_key="4BFOLKEREG",
)

SECURITY_UNIT = Department(
    id=818485,
    name="Borgerservice",
    user_key="4BBORGER",
)

CASEWORKER = Caseworker(
    name="Rpabruger Rpa78 - MÅ IKKE SLETTES RITM0531920",
    ident="AZRPAB1",
    uuid="9c35b5a5-4f9a-410d-aba6-c42595890a76",
    type="user",
)

DOCUMENT_TYPE = "Indgående"
DOCUMENT_SENSITIVITY = "Følsomme"
DOCUMENT_CATEGORY_NAME = "Ansøgning"
DOCUMENT_CATEGORY_UUID = "0292ea5d-616c-44e8-9469-af7b7b546ec8"

TASK_TITLE = "Uden fast bopæl i en midlertidig periode (fra Selvbetjening.aarhuskommune.dk)"
