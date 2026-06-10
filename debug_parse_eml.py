"""Offline debug helper for the mail-parsing logic.

Parses a saved ``.eml`` file and runs the robot's sender/subject filtering and
CPR extraction on it, without touching the network, KMD Nova or Graph. Useful
for quickly verifying that a given mail matches the filter and that the CPR
number is extracted correctly.

Usage::

    python debug_parse_eml.py [sti/til/mail.eml]

If no path is given, the bundled sample at tests/samples/ufb_eksempel.eml is used.
"""

import email
import sys
from email.policy import default as default_policy
from pathlib import Path

from itk_dev_shared_components.graph.mail import Email

from robot_framework.exceptions import BusinessError
from robot_framework.process import _extract_cpr, _filter_emails

SAMPLE_EML = Path(__file__).parent / "tests" / "samples" / "ufb_eksempel.eml"


def load_eml(path: Path) -> Email:
    """Parse an .eml file into a graph_mail.Email object."""
    with open(path, "rb") as file:
        message = email.message_from_binary_file(file, policy=default_policy)

    body_part = message.get_body(preferencelist=("plain", "html"))
    if body_part is not None:
        body = body_part.get_content()
        body_type = "html" if body_part.get_content_subtype() == "html" else "text"
    else:
        body = ""
        body_type = "text"

    return Email(
        user=message["to"] or "",
        id="debug",
        received_time=message["date"] or "",
        sender=message["from"] or "",
        receivers=[message["to"] or ""],
        subject=message["subject"] or "",
        body=body,
        body_type=body_type,
        has_attachments=False,
    )


def main() -> None:
    """Parse the given (or sample) .eml and report filter + CPR results."""
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else SAMPLE_EML
    print(f"Parsing: {path}")

    mail = load_eml(path)
    print(f"  Sender:  {mail.sender}")
    print(f"  Subject: {mail.subject}")

    passes_filter = bool(_filter_emails((mail,)))
    print(f"  Matches sender + UFB subject filter: {passes_filter}")

    try:
        cpr = _extract_cpr(mail)
        print(f"  Extracted CPR: {cpr}")
    except BusinessError as error:
        print(f"  CPR extraction failed: {error}")


if __name__ == "__main__":
    main()
