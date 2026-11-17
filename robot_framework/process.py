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
from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.kmd_nova import nova_cases, nova_documents, nova_tasks
from itk_dev_shared_components.kmd_nova.nova_objects import NovaCase, CaseParty, Document, Task
from itk_dev_shared_components.graph import authentication as graph_authentication
from itk_dev_shared_components.graph import mail as graph_mail
from itk_dev_shared_components.graph.authentication import GraphAccess

from robot_framework import config
from robot_framework.exceptions import BusinessError

# Matches a Danish CPR number with or without the separating dash.
CPR_PATTERN = re.compile(r"\b(\d{6}-?\d{4})\b")


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")

    nova_credential = orchestrator_connection.get_credential(config.NOVA_API)
    nova_access = NovaAccess(client_id=nova_credential.username, client_secret=nova_credential.password)

    graph_credential = orchestrator_connection.get_credential(config.GRAPH_API)
    graph_access = graph_authentication.authorize_by_username_password(
        graph_credential.username, **json.loads(graph_credential.password)
    )

    emails = graph_mail.get_emails_from_folder(config.MAILBOX, config.SOURCE_FOLDER, graph_access)
    emails = _filter_emails(emails)
    emails = sorted(emails, key=lambda email: email.received_time)

    if not emails:
        orchestrator_connection.log_info("No 'Uden fast bopæl' mails to journalize. Stopping.")
        return

    orchestrator_connection.log_info(f"Found {len(emails)} mail(s) to journalize.")

    for email in emails:
        _handle_email(email, nova_access, graph_access, orchestrator_connection)


def _handle_email(email: graph_mail.Email, nova_access: NovaAccess, graph_access: GraphAccess,
                  orchestrator_connection: OrchestratorConnection) -> None:
    """Create a case, journalize the mail, create a task and move the mail.

    Note: the steps are not transactional. If a step after case creation fails,
    a retry will create a duplicate case. This matches the PDD (always create a
    new case) but is worth keeping in mind.
    """
    cpr = _extract_cpr(email)

    orchestrator_connection.log_trace("Creating case in KMD Nova.")
    case = _create_case(cpr, nova_access)

    orchestrator_connection.log_trace("Journalizing mail on case.")
    _journalize_mail(email, case, nova_access, graph_access)

    orchestrator_connection.log_trace("Creating task on case.")
    _create_task(case, nova_access)

    orchestrator_connection.log_trace("Moving mail to done folder.")
    graph_mail.move_email(email, config.DONE_FOLDER, graph_access)


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


def _create_case(cpr: str, nova_access: NovaAccess) -> NovaCase:
    """Create and add a 'Folkeregistrering i almindelighed' case for the citizen."""
    case = NovaCase(
        uuid=str(uuid.uuid4()),
        title=config.CASE_TITLE,
        case_date=datetime.now(),
        progress_state="Opstaaet",
        case_parties=[CaseParty(role="Primær", identification_type="CprNummer", identification=cpr, name="Test Test")],
        kle_number=config.KLE_NUMBER,
        proceeding_facet=config.PROCEEDING_FACET,
        sensitivity=config.CASE_SENSITIVITY,
        caseworker=config.CASEWORKER,
        responsible_department=config.RESPONSIBLE_DEPARTMENT,
        security_unit=config.SECURITY_UNIT,
    )
    nova_cases.add_case(case, nova_access)
    return case


def _journalize_mail(email: graph_mail.Email, case: NovaCase, nova_access: NovaAccess, graph_access: GraphAccess) -> None:
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
        caseworker=config.CASEWORKER,
    )
    nova_documents.attach_document_to_case(
        case.uuid, document, nova_access,
        security_unit_id=config.SECURITY_UNIT.id,
        security_unit_name=config.SECURITY_UNIT.name,
    )


def _create_task(case: NovaCase, nova_access: NovaAccess) -> None:
    """Create a task on the case with today as the deadline."""
    task = Task(
        uuid=str(uuid.uuid4()),
        title=config.TASK_TITLE,
        caseworker=config.CASEWORKER,
        status_code="N",
        deadline=datetime.now(),
    )
    nova_tasks.attach_task_to_case(case.uuid, task, nova_access)


def _safe_file_name(name: str) -> str:
    """Strip characters that are not allowed in file names."""
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return cleaned or "dokument"


if __name__ == '__main__':
    import os
    import uuid
    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("Uden fast bopæl", conn_string, crypto_key, '', "trigger_id", uuid.uuid4())
    process(oc)
