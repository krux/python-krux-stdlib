# -*- coding: utf-8 -*-
#
# © 2014 Krux Digital, Inc.
#
"""
Classes & Functions for email.
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from email.mime.text import MIMEText

# I import all of these exception types so that users of the sendmail
# function can import them from this module instead of magically knowing
# where they come from in the standard library.
from smtplib import (
    SMTP,
    SMTPException,
    SMTPServerDisconnected,
    SMTPResponseException,
    SMTPSenderRefused,
    SMTPRecipientsRefused,
    SMTPDataError,
    SMTPConnectError,
    SMTPHeloError,
    SMTPAuthenticationError,
)

#####################
# General Libraries #
#####################
import pystache

####################
# Internal Imports #
####################


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
    if isinstance(recipients, basestring):
        recipients = [ recipients ]

    if bcc is None:
        bcc = []

    if isinstance(bcc, basestring):
        bcc = [ bcc ]

    if headers is None:
        headers = {}

    if template_args is None:
        template_args = {}

    if smtp_host is None:
        smtp_host = 'localhost'

    if smtp_connection is None:
        smtp_connection = SMTP(smtp_host)

    # Render the subject/body templates. We have to ascii-encode the
    # results because the call to email.as_string below will fail if either
    # of these contain utf8-encoded substrings.
    #
    # We just ignore any characters that can't be ASCII-encoded.
    subject = pystache.render(subject, template_args).encode('ascii', 'ignore')
    body = pystache.render(body, template_args).encode('ascii', 'ignore')

    # Construct the email message object.
    email = MIMEText(body)
    email[ 'Subject' ] = subject
    email[ 'From' ] = sender
    email[ 'To' ] = ','.join(recipients)

    # Add additional headers requested by the user.
    for header, value in headers.iteritems():
        email[header] = value

    # Send the email to the primary recipients and to the BCC'ed recipients
    smtp_connection.sendmail(sender, recipients + bcc, email.as_string())
