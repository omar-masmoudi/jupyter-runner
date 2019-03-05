from jupyter_runner.mail import (
    MailConfiguration,
)


def test_mail_configuration():
    args = {
        '--mail-to': 'a@x.com , b@x.com',
        '--mail-cc': None,
        '--mail-bcc': None,
        '--mail-from': 'jupyter-runner',
        '--mail-subject': 'jupyter-runner report',
        '--mail-message': 'Please check attached reports.',
        '--mail-html-inline': False,
        '--mail-host': 'localhost',
        '--mail-port': '25',
        '--mail-do-not-compress': False,
        '--any-other-option': 'any_value',  # Ignore additional options
    }

    # Parse MailConfiguration from args
    conf = MailConfiguration(args)

    # Ensure object is built as expected
    assert conf.mail_to == 'a@x.com , b@x.com'
    assert conf.mail_cc is None
    assert conf.mail_bcc is None
    assert conf.mail_from == 'jupyter-runner'
    assert conf.mail_subject == 'jupyter-runner report'
    assert conf.mail_html_inline is False
    assert conf.mail_host == 'localhost'
    assert conf.mail_port == 25
    assert conf.mail_do_not_compress is False
