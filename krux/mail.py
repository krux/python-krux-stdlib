# Copyright 2013-2020 Salesforce.com, inc.
"""
Classes & Functions for email.
"""
from __future__ import generator_stop

from email.header import Header
from email.mime.text import MIMEText
from smtplib import SMTP

import pystache

CHARSET = 'utf-8'


def ascii_encodable(text):
    """
    Return True if the given TEXT can be losslessly encoded in
    ASCII. Otherwise, return False.
    """
    return all(ord(char) < 128 for char in text)


def add_header(message, name, value):
    """
    Add a (properly encoded) header NAME with value VALUE to the given
    MESSAGE object.
    """
    if not ascii_encodable(value):
        value = Header(value, CHARSET)

    message[name] = value


def sendmail(
        sender,
        recipients,
        subject,
        body,
        bcc=None,
        headers=None,
        template_args=None,
        smtp_host=None,
        smtp_connection=None,
):
    """
    Send an email.

    SENDER will be used as the envelope 'From' in the resulting email.

    RECIPIENTS can be an email address or a list of email addresses; these
    will be the recipients of the email.

    SUBJECT will be rendered using pystache.render and the given
    TEMPLATE_ARGS (if any); the result will be used as the subject line of
    the email.

    BODY will be rendered using pystache.render and the given TEMPLATE_ARGS
    (if any); the result will be used as the body of the email.

    BCC is optional; if given this should be an email address or a list of
    email addresses; these will be BCC'ed on the email.

    HEADERS is optional; if given this should be a dict-like object of
    headers which will be added to the email.

    TEMPLATE_ARGS is optional; if given this should be a dict-like object
    which will be passed to pystache.render to be interpolated in the
    subject/body templates. Default: {}

    SMTP_HOST is optional; if given, this should be a string specifying the
    SMTP host to connect to. Default: localhost

    SMTP_CONNECTION is optional; if given, this should be an object
    implementing the same interface as smtplib.SMTP. By default, an
    smtplib.SMTP object will be created, connecting to SMTP_HOST.

    If SMTP_CONNECTION is not given, this function may raise an
    smtplib.SMTPConnectError - see the smtplib documentation for details.

    This function may raise an smtplib.SMTPException for many failure cases
    - see the smtplib documentation for details.

    This function returns an email.mime.MIMEText object representing the
    email that was sent.
    """
    if isinstance(recipients, str):
        recipients = [recipients]

    if bcc is None:
        bcc = []

    if isinstance(bcc, str):
        bcc = [bcc]

    if headers is None:
        headers = {}

    if template_args is None:
        template_args = {}

    if smtp_host is None:
        smtp_host = 'localhost'

    if smtp_connection is None:
        smtp_connection = SMTP(smtp_host)

    # Render the subject/body templates.
    subject = pystache.render(subject, template_args)
    body = pystache.render(body, template_args)

    # Construct the email message object. This is a plain-text email
    # ('plain' arg.)
    #
    # We have to make sure we handle encoding correctly, so we check if the
    # text can be ASCII-encoded, and use the global CHARSET otherwise.
    if ascii_encodable(body):
        email = MIMEText(body, 'plain')
    else:
        email = MIMEText(body.encode(CHARSET), 'plain', CHARSET)

    # Add the basic mail headers. They will be properly encoded by
    # add_header.
    add_header(email, 'Subject', subject)
    add_header(email, 'From', sender)
    add_header(email, 'To', ','.join(recipients))

    # Add additional headers requested by the user.
    for header, value in list(headers.items()):
        add_header(email, header, value)

    # Send the email to the primary recipients and to the BCC'ed recipients
    smtp_connection.sendmail(sender, recipients + bcc, email.as_string())
