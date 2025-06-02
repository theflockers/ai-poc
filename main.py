import os
import requests
import json
import smtplib
from email.mime.text import MIMEText


subject = "Release Service update"
sender = "theflockers@gmail.com"
recipients = "lmendes@redhat.com"
password = open("%s/gmail-pass.txt" % os.getenv("HOME")).read()


def print_contents(contents):
    data = ""
    jsonData = json.loads(contents)
    for candidate in jsonData["candidates"]:
        for part in candidate["content"]["parts"]:
            data += part["text"]

    return data


def ask_gemini(endpoint, key, text):
    url = "%s?key=%s" % (endpoint, key)

    data = {"contents": [
        {"parts":
         [{"text": text}]}
    ]}
    return requests.post(url, json=data).text


def get_envelope(sender, recipient, subject, html):
    html = html.removeprefix("```html").removesuffix("```")
    msg = MIMEText(html, 'html')
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    return msg


def email(sender, subject, recipient, text):
    msg = get_envelope(sender, recipient, subject, text)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password.strip())
        smtp_server.sendmail(sender, recipient, msg.as_string())


def main():
    GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/" \
            "gemini-2.0-flash:generateContent"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    commit_data = open("commits.tmp").read()
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
    print(response)
    email(sender, subject, recipients, print_contents(response))


if __name__ == "__main__":
    main()
