import logging
import tempfile
import os
import smtplib
import zipfile
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

from .file_handler import LocalFile


LOGGER = logging.getLogger(__file__)


class MailConfiguration:
    """Mail configuration class."""

    def __init__(self, args):
        """Init an EmailConfiguration object from jupyter-runner cli args.

        :param args: jupyter-runner cli configuration
        """
        # Mail destination
        self.mail_to = args['--mail-to']
        self.mail_cc = args['--mail-cc']
        self.mail_bcc = args['--mail-bcc']

        # If any of destination address is set, do the e-mail sending
        self.send_mail = bool(self.mail_to or self.mail_cc or self.mail_bcc)

        # Additional e-mail options
        self.mail_from = args['--mail-from']
        self.mail_subject = args['--mail-subject']
        self.mail_message = args['--mail-message']
        self.mail_html_inline = args['--mail-html-inline']
        self.mail_do_not_compress = args['--mail-do-not-compress']

        # Technical e-mail options
        self.mail_host = args['--mail-host']
        self.mail_port = int(args['--mail-port'])

    @staticmethod
    def _parse_mail_list(mail_str):
        """Parse mail string and return list.

        :param mail_str: Comma separated list or None
        :return: list of str or None
        """
        if not mail_str:
            return None

        return [addr.strip() for addr in mail_str.split(',')]


def _prepare_attachments(msg,
                         filenames,
                         mail_configuration,
                         zip_file,
                         html_content):
    """Prepare mail attachments for a list of filenames.

    :param msg: MIMEMultipart object
    :param filenames: list of filenames (S3 or local)
    :param mail_configuration: MailConfiguration object
    :param zip_file: ZipFile object to write to
    :param html_content: List of html content used to append in place
    """
    for filename in filenames:
        with LocalFile(filename) as local_filename:
            bname = os.path.basename(local_filename)

            with open(local_filename, mode='rb') as file_obj:
                # Open local or S3 file locally
                content = file_obj.read()
                part = MIMEApplication(
                    content,
                    Name=bname,
                )

                # Prepare inline of HTML files
                _, extension = os.path.splitext(bname)
                if extension.lower() == '.html':
                    html_content.append(content.decode())

            if not mail_configuration.mail_do_not_compress:
                # Prepare zip archive
                zip_file.write(local_filename,
                               bname,
                               compress_type=zipfile.ZIP_LZMA)

            # After the file is closed, add the attachment
            if mail_configuration.mail_do_not_compress:
                # Don't use the zip archive and attach single files
                part['Content-Disposition'] = \
                    'attachment; filename="%s"' % bname
                LOGGER.info("Attaching %s", bname)
                msg.attach(part)


def send_email(
        filenames,
        mail_configuration,
):
    """Send email given attachment filenames and mail configuration.

    :param filenames: list of filenames (S3 or local)
    :param mail_configuration: MailConfiguration object
    """
    msg = MIMEMultipart()
    msg['Subject'] = mail_configuration.mail_subject
    if mail_configuration.mail_to:
        msg['To'] = mail_configuration.mail_to
    if mail_configuration.mail_cc:
        msg['Bcc'] = mail_configuration.mail_cc
    if mail_configuration.mail_bcc:
        msg['Cc'] = mail_configuration.mail_bcc

    msg['From'] = mail_configuration.mail_from

    # Push html content found in attachments
    html_content = []

    # Construct mail attachments and inline HTML content
    with tempfile.TemporaryDirectory() as zip_dir:
        zip_name = 'attachments.zip'
        with zipfile.ZipFile(
                os.path.join(zip_dir, zip_name),
                mode='w',
                compression=zipfile.ZIP_LZMA,
        ) as zip_file:
            # loop through attachments
            _prepare_attachments(msg=msg,
                                 filenames=filenames,
                                 mail_configuration=mail_configuration,
                                 zip_file=zip_file,
                                 html_content=html_content)

        if not mail_configuration.mail_do_not_compress:
            # Attach the zip archive
            with open(os.path.join(zip_dir, zip_name), mode='rb') as file_obj:
                # Open local or S3 file locally
                content = file_obj.read()
                part = MIMEApplication(
                    content,
                    Name=zip_name,
                )
            part['Content-Disposition'] = \
                'attachment; filename="%s"' % zip_name
            LOGGER.info("Attaching %s", zip_name)
            msg.attach(part)

        if html_content and mail_configuration.mail_html_inline:
            # Add HTML text by joining all html files
            part = MIMEText('<hr>'.join(html_content), 'html')
            LOGGER.info("Attaching HTML inline content")
            msg.attach(part)
        else:
            part = MIMEText(mail_configuration.mail_message, 'plain')
            LOGGER.info("Attaching plain text message: %s",
                        mail_configuration.mail_message)
            msg.attach(part)

        with smtplib.SMTP(host=mail_configuration.mail_host,
                          port=mail_configuration.mail_port) as smtp_con:
            LOGGER.info("Sending e-mail with report attached.")
            LOGGER.debug("Mail message: %s", msg)
            smtp_con.send_message(msg)
