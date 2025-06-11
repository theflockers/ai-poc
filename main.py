import os
import requests
import json
import smtplib
import subprocess
import tempfile
from email.mime.text import MIMEText


class Mail:
    __sender = ""
    __recipients = ""
    __subject = ""
    __smtphost = ""
    __smtpport = 465
    __password = ""

    def __init__(self):
        self.__load_env()

    def __load_env(self):
        self.__recipients = os.getenv("MAIL_RECIPIENTS")
        self.__sender = os.getenv("MAIL_SENDER")
        self.__subject = os.getenv("MAIL_SUBJECT")
        self.__smtphost = os.getenv("MAIL_SMTPHOST")
        self.__smtpport = os.getenv("MAIL_SMTPPORT")
        self.__smtppass = os.getenv("MAIL_SMTPPASS")

    def get_sender(self):
        return self.__sender

    def get_recipients(self):
        return self.__recipients

    def get_subject(self):
        return self.__subject

    def get_smtphost(self):
        return self.__smtphost

    def get_smtpport(self):
        return self.__smtpport

    def get_smtppass(self):
        return self.__smtppass.strip()

    def __get_envelope(self, html):
        html = html.removeprefix("```html").removesuffix("```")
        msg = MIMEText(html, 'html')
        msg["Subject"] = self.get_subject()
        msg["From"] = self.get_sender()
        msg["To"] = self.get_recipients()
        return msg

    def send(self, body):
        msg = self.__get_envelope(body)
        with smtplib.SMTP_SSL(
            self.get_smtphost(),
            self.get_smtpport()
        ) as smtp_server:
            smtp_server.login(self.get_sender(), self.get_smtppass())
            smtp_server.sendmail(self.get_sender(),
                                 self.get_recipients(), msg.as_string())


class Git:
    __git_repo = ""
    __git_apikey = ""
    __tempdir = ""

    def __init__(self):
        self.__load_env()
        with tempfile.TemporaryDirectory(delete=False) as tempdir:
            self.__tempdir = tempdir

    def __load_env(self):
        self.__git_repo = os.getenv("GIT_REPO")

    def __get_git_repo_dir(self):
        import re
        preg = re.compile("(.*)//(.*)/(.*)/(.*)")
        parts = preg.search(self.get_git_repo().removesuffix(".git"))
        return parts[4]

    def get_local_git_repo(self):
        return "%s/%s" % (self.get_tempdir(), self.__get_git_repo_dir())

    def get_tempdir(self):
        return self.__tempdir

    def __clone(self):
        os.chdir(self.get_tempdir())
        subprocess.run(["/usr/bin/git", "clone",
                        "--depth", "50",
                        self.get_git_repo()])

    def pull(self):
        self.__clone()
        os.chdir(self.get_local_git_repo())
        subprocess.run(["git", "pull"])

    def get_git_repo(self):
        return self.__git_repo

    def log(self, days_in_past=0):
        import datetime as dt
        today = dt.date.today()
        since = today - dt.timedelta(days=days_in_past)
        since_fmt = since.strftime("%Y-%m-%d")
        commit_log_path = "%s/%s" % (self.get_tempdir(), "commit.tmp")
        commit_log = open(commit_log_path, "w+")
        subprocess.run(["git", "log", "--since", since_fmt], stdout=commit_log)
        commit_log.close()

        return commit_log_path


def ask_gemini(endpoint, key, text):
    url = "%s?key=%s" % (endpoint, key)

    data = {"contents": [
        {"parts":
         [{"text": text}]}
    ]}
    print("Request to Gemini made...")
    return requests.post(url, json=data).text


def get_contents(contents):
    data = ""
    jsonData = json.loads(contents)
    for candidate in jsonData["candidates"]:
        for part in candidate["content"]["parts"]:
            data += part["text"]

    return data


def main():
    GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/" \
            "gemini-2.0-flash:generateContent"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    git = Git()
    git.pull()
    commit_data = open(git.log(7)).read()

    question = "generate a short html e-mail in behalf of the Release" \
        " Service Team explaining in a simple form what is changing, also " \
        "correcting the grammar when necessary, but " \
        "please include the ticket names which are in the format " \
        "RELEASE-XXXX, linking them to https://issues.redhat.com/browse/ " \
        "with the ticket name\n" \
        "close the message with a pun based on the work done as the " \
        "\"AI Generated Pun\"" \
        "The commit list is: \n%s" % (commit_data)

    response = ask_gemini(GEMINI_API, GEMINI_API_KEY, question)

    mail = Mail()
    mail.send(get_contents(response))
    print("message sent")


if __name__ == "__main__":
    main()
