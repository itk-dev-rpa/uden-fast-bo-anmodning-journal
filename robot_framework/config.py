"""This module contains configuration constants used across the framework"""

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


# Queue specific configs
# ----------------------

# The name of the job queue (if any)
QUEUE_NAME = None

# The limit on how many queue elements to process
MAX_TASK_COUNT = 100

# ----------------------


# Process specific configs
# ----------------------

# Mailbox that holds the source folder. The robot authenticates with the Graph
# credential and reads this user's mailbox.
MAILBOX = "itk-rpa@ba.aarhus.dk"

# Outlook folders (paths relative to the mailbox root).
SOURCE_FOLDER = "Selvbetjening UA og UFB"
DONE_FOLDER = "Slettetmappen 6"

# Only mails from this sender should be journalized (PDD step 5).
VALID_SENDER = "selvbetjening.aarhuskommune.dk"

# The "Selvbetjening UA og UFB" folder also holds UA mails, so the subject is
# used to pick out the "Uden fast bopæl" (UFB) mails.
VALID_SUBJECTS = (
    "Uden fast bopæl i en midlertidig periode (fra Selvbetjening.aarhuskommune.dk)",
    "Webform submission from: Without permanent residence",
)

# KMD Nova case settings.
CASE_TITLE = "Folkeregistrering i almindelighed"
KLE_NUMBER = "23.05.00"
PROCEEDING_FACET = "G01"
CASE_SENSITIVITY = "Følsomme"

# Department that is responsible for the case (4BFOLKEREG Folkeregister og Sygesikring).
RESPONSIBLE_DEPARTMENT_ID = 70403
RESPONSIBLE_DEPARTMENT_NAME = "Folkeregister og Sygesikring"
RESPONSIBLE_DEPARTMENT_USER_KEY = "4BFOLKEREG"

# Security unit for the case and documents (4BBORGER Borgerservice).
SECURITY_UNIT_ID = 818485
SECURITY_UNIT_NAME = "Borgerservice"
SECURITY_UNIT_USER_KEY = "4BBORGER"

# Caseworker the robot acts as / assigns the task to. Temporary robot account
# until the dedicated caseworker account (RITM0283472) is ready.
CASEWORKER_NAME = "AZRPA78 - Rpabruger Rpa78 - MÅ IKKE SLETTES RITM0283472"
CASEWORKER_IDENT = "AZRPA78"
CASEWORKER_UUID = "a577c0a2-a131-43a5-b4e6-b4f5bb75028f"
CASEWORKER_TYPE = "group"

# Document settings (PDD step 16: type 'Indgående', category 'Ansøgning').
DOCUMENT_TYPE = "Indgående"
DOCUMENT_SENSITIVITY = "Følsomme"
# Nova only accepts the category by UUID, not by name.
# TODO: Get the category UUID for "Ansøgning" from fagperson and insert it here.
DOCUMENT_CATEGORY_NAME = "Ansøgning"
DOCUMENT_CATEGORY_UUID = None

# Task settings (PDD step 19).
TASK_TITLE = "Uden fast bopæl i en midlertidig periode (fra Selvbetjening.aarhuskommune.dk)"

# ----------------------
