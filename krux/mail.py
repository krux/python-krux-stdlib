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

    This function returns an email.mime.MimeText object representing the
    email that was sent.
    """
    if template_args is None:
        template_args = {}

    if smtp_host is None:
        smtp_host = 'localhost'

    if smtp_connection is None:
        smtp_connection = SMTP(smtp_host)

    if isinstance(recipients, basestring):
        recipients = [ recipients ]

    # Render the subject/body templates.
    subject = pystache.render(subject, template_args)
    body = pystache.render(body, template_args)

    # Construct the email message object.
    email = MimeText(body)
    email[ 'Subject' ] = subject
    email[ 'From' ] = sender
    email[ 'To' ] = ','.join(recipients)

    # Send the email.
    smtp_connection.sendmail(sender, recipients, email.as_string())
