"""This module contains the main process of the robot.

The robot reads "Uden fast bopæl" self-service mails from a shared Outlook folder,
creates a case in KMD Nova for the citizen, journalizes the mail on the case,
creates a task on the case and finally moves the mail to a done folder.
"""

import json
import re
import uuid
from datetime import datetime

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from OpenOrchestrator.database.queues import QueueElement

from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.kmd_nova import nova_cases, nova_documents, nova_tasks
from itk_dev_shared_components.kmd_nova.nova_objects import (
    NovaCase, CaseParty, Caseworker, Department, Document, Task,
)
from itk_dev_shared_components.graph import authentication as graph_authentication
from itk_dev_shared_components.graph import mail as graph_mail
from itk_dev_shared_components.graph.authentication import GraphAccess

from robot_framework import config
from robot_framework.exceptions import BusinessError

# Matches a Danish CPR number with or without the separating dash.
CPR_PATTERN = re.compile(r"\b(\d{6}-?\d{4})\b")


# pylint: disable-next=unused-argument
def process(orchestrator_connection: OrchestratorConnection, queue_element: QueueElement | None = None) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")

    nova_access = _get_nova_access(orchestrator_connection)
    graph_access = _get_graph_access(orchestrator_connection)
    caseworker = Caseworker(
        uuid=config.CASEWORKER_UUID,
        name=config.CASEWORKER_NAME,
        ident=config.CASEWORKER_IDENT,
        type=config.CASEWORKER_TYPE,
    )

    emails = graph_mail.get_emails_from_folder(config.MAILBOX, config.SOURCE_FOLDER, graph_access)
    emails = _filter_emails(emails)
    # Process the oldest mail first (received_time is an ISO 8601 string, so a
    # lexicographic sort is also chronological).
    emails = sorted(emails, key=lambda email: email.received_time)

    if not emails:
        orchestrator_connection.log_info("No 'Uden fast bopæl' mails to journalize. Stopping.")
        return

    orchestrator_connection.log_info(f"Found {len(emails)} mail(s) to journalize.")

    for email in emails:
        _handle_email(email, caseworker, nova_access, graph_access, orchestrator_connection)


def _handle_email(email: graph_mail.Email, caseworker: Caseworker, nova_access: NovaAccess,
                  graph_access: GraphAccess, orchestrator_connection: OrchestratorConnection) -> None:
    """Create a case, journalize the mail, create a task and move the mail.

    Note: the steps are not transactional. If a step after case creation fails,
    a retry will create a duplicate case. This matches the PDD (always create a
    new case) but is worth keeping in mind.
    """
    cpr = _extract_cpr(email)

    orchestrator_connection.log_trace("Creating case in KMD Nova.")
    case = _create_case(cpr, caseworker, nova_access)

    orchestrator_connection.log_trace("Journalizing mail on case.")
    _journalize_mail(email, case, caseworker, nova_access, graph_access)

    orchestrator_connection.log_trace("Creating task on case.")
    _create_task(case, caseworker, nova_access)

    orchestrator_connection.log_trace("Moving mail to done folder.")
    graph_mail.move_email(email, config.DONE_FOLDER, graph_access)


def _get_nova_access(orchestrator_connection: OrchestratorConnection) -> NovaAccess:
    """Build a NovaAccess from the Nova API credential."""
    credential = orchestrator_connection.get_credential(config.NOVA_API)
    return NovaAccess(client_id=credential.username, client_secret=credential.password)


def _get_graph_access(orchestrator_connection: OrchestratorConnection) -> GraphAccess:
    """Build a GraphAccess from the Graph API credential.

    The credential's password field is a JSON object holding password, client_id
    and tenant_id, while the username field holds the login username.
    """
    credential = orchestrator_connection.get_credential(config.GRAPH_API)
    return graph_authentication.authorize_by_username_password(credential.username, **json.loads(credential.password))


def _filter_emails(emails: tuple[graph_mail.Email]) -> list[graph_mail.Email]:
    """Keep only mails from the self-service sender with a valid UFB subject.

    The source folder also contains UA mails, so the subject is used to pick out
    the "Uden fast bopæl" mails.
    """
    return [
        email for email in emails
        if config.VALID_SENDER in email.sender.lower()
        and email.subject.strip() in config.VALID_SUBJECTS
    ]


def _extract_cpr(email: graph_mail.Email) -> str:
    """Extract the citizen's CPR number from the mail body (without dash)."""
    text = email.get_text()
    # Prefer a number that follows a "CPR" label to avoid matching e.g. phone numbers.
    labeled = re.search(r"CPR[^\d]{0,20}(\d{6}-?\d{4})", text, re.IGNORECASE)
    match = labeled or CPR_PATTERN.search(text)
    if not match:
        raise BusinessError(f"No CPR number found in mail '{email.subject}'.")
    return match.group(1).replace("-", "")


def _create_case(cpr: str, caseworker: Caseworker, nova_access: NovaAccess) -> NovaCase:
    """Create and add a 'Folkeregistrering i almindelighed' case for the citizen."""
    case = NovaCase(
        uuid=str(uuid.uuid4()),
        title=config.CASE_TITLE,
        case_date=datetime.now(),
        progress_state="Opstaaet",
        case_parties=[CaseParty(role="Primær", identification_type="CprNummer", identification=cpr)],
        kle_number=config.KLE_NUMBER,
        proceeding_facet=config.PROCEEDING_FACET,
        sensitivity=config.CASE_SENSITIVITY,
        caseworker=caseworker,
        responsible_department=Department(
            id=config.RESPONSIBLE_DEPARTMENT_ID,
            name=config.RESPONSIBLE_DEPARTMENT_NAME,
            user_key=config.RESPONSIBLE_DEPARTMENT_USER_KEY,
        ),
        security_unit=Department(
            id=config.SECURITY_UNIT_ID,
            name=config.SECURITY_UNIT_NAME,
            user_key=config.SECURITY_UNIT_USER_KEY,
        ),
    )
    nova_cases.add_case(case, nova_access)
    return case


def _journalize_mail(email: graph_mail.Email, case: NovaCase, caseworker: Caseworker,
                     nova_access: NovaAccess, graph_access: GraphAccess) -> None:
    """Upload the mail as a document and attach it to the case."""
    mime = graph_mail.get_email_as_mime(email, graph_access)
    file_name = f"{_safe_file_name(email.subject)}.eml"
    document_uuid = nova_documents.upload_document(mime, file_name, nova_access)

    document = Document(
        uuid=document_uuid,
        title=email.subject,
        sensitivity=config.DOCUMENT_SENSITIVITY,
        document_type=config.DOCUMENT_TYPE,
        description=email.subject,
        approved=True,
        category_name=config.DOCUMENT_CATEGORY_NAME,
        category_uuid=config.DOCUMENT_CATEGORY_UUID,
        file_extension="eml",
        caseworker=caseworker,
    )
    nova_documents.attach_document_to_case(
        case.uuid, document, nova_access,
        security_unit_id=config.SECURITY_UNIT_ID,
        security_unit_name=config.SECURITY_UNIT_NAME,
    )


def _create_task(case: NovaCase, caseworker: Caseworker, nova_access: NovaAccess) -> None:
    """Create a task on the case with today as the deadline."""
    task = Task(
        uuid=str(uuid.uuid4()),
        title=config.TASK_TITLE,
        caseworker=caseworker,
        status_code="N",
        deadline=datetime.now(),
    )
    nova_tasks.attach_task_to_case(case.uuid, task, nova_access)


def _safe_file_name(name: str) -> str:
    """Strip characters that are not allowed in file names."""
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return cleaned or "dokument"
