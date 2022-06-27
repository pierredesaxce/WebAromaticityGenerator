from __future__ import print_function

import atexit
import base64
import io
import os
import os.path
import os.path
import sys

import paramiko
from apscheduler.schedulers.background import BackgroundScheduler
from aromaGraph import create_projection  # may need to implement the method directly instead of having the whole file
from flask import Flask, render_template, request
from flask_mail import Mail
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

app = Flask(__name__)

try:
    file = open("token", "r")
except:
    print("donnees de connexion au cluster manquantes")
    sys.exit(1)

username = file.readline()
username = username[:-1]
password = file.readline()
password = password[:-1]
gmail_address = file.readline()
gmail_address = gmail_address[:-1]
gmail_password = file.readline()

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname="10.184.4.20", username=username, password=password, allow_agent=False, look_for_keys=False)

running_subg16_job_mail = {}
aromaticity_fig_result = {}

app.config.update(
    DEBUG=True,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=gmail_address,
    MAIL_PASSWORD=gmail_password
)

mail = Mail(app)


def google_connect():  # DON'T ASK ME ABOUT THAT DOGSHIT. FUCK GOOGLE
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        if not labels:
            print('No labels found.')
            return
        print('Labels:')
        for label in labels:
            print(label['name'])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


def check_subg16_job_status():  # THIS NEED TO BE CHANGED but keep the code it will be useful later
    with app.app_context():
        job_done = []
        for job_id in running_subg16_job_mail:
            stdin, stdout, stderr = ssh_client.exec_command("/usr/bin/sacct -p -j " + job_id)
            output = stdout.readlines()
            output_status = (output[-1].split("|"))[-3]
            print(output_status)
            if output_status == "FAILED":
                msg = mail.send_message(
                    "Resultat calcul d\'aromaticité",
                    sender=gmail_address,
                    recipients=[running_subg16_job_mail[job_id]],
                    body="Votre calcul d'aromaticité à échoué. Re-essayez et vérifiez que le document envoyé est "
                         "correct")
                job_done.append(job_id)
            elif output_status == "COMPLETED":
                png_image = io.BytesIO()
                FigureCanvas(create_projection("./output/test.txt")).print_png(png_image)
                pngImageB64String = "data:image/png;base64,"
                pngImageB64String += base64.b64encode(png_image.getvalue()).decode('utf8')
                aromaticity_fig_result[0] = pngImageB64String
                msg = mail.send_message(
                    "Resultat calcul d\'aromaticité",
                    sender=gmail_address,
                    recipients=[running_subg16_job_mail[job_id]],
                    body="Votre calcul d'aromaticité ( id = " + job_id + ") vient de se terminer. Retrouvez les "
                                                                         "résultats à l'adresse : " +
                         "http://localhost:5000/result/" + job_id)
                job_done.append(job_id)

        for job in job_done:  # remove all job completed
            running_subg16_job_mail.pop(job)

            """context = ssl.create_default_context()

            sender_email = "aromaticitybot@gmail.com"
            receiver_email = "pierredesaxce@gmail.com"
            message = "texte : " + running_subg16_job_mail[job_id]

            with smtplib.SMTP("localhost", port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message)"""


@app.route('/result/<id>')
def show_result(id):
    nfile_name = 'inputMolecule.log'

    ftp_client = ssh_client.open_sftp()
    ftp_client.get("/home/" + username + "/slurm-output/" + id + "/" + nfile_name, "./output/" + id + ".log")
    ftp_client.close()

    try:
        output_file = open("./output/" + id + ".log", "r")
    except:
        print("output_file missing")
        sys.exit(1)

    result = "".join(output_file.readlines())

    return render_template("result.html", result=result)


@app.route("/confirmation", methods=['POST'])
def confirm():
    render_template("confirmation.html")

    post_file = request.files['inputFile']

    nfile_name = 'inputMolecule.com'

    nfile = open(nfile_name, 'w+')  # open file in append mode
    nfile.write("# opt B3LYP/6-31g\n\ni'm a commentary\n\n")

    count = 0
    for line in post_file.readlines():
        if line[0] == "C":
            count = count + 1

    if count % 2 == 0:
        nfile.write("0 1\n")
    else:
        nfile.write("0 2\n")

    post_file.seek(0)
    post_file.readline()
    post_file.readline()
    for line in post_file.readlines():
        nfile.write(line.decode('UTF-8'))
        print(line.decode('UTF-8'))  # need decode cause line is type Byte not String

    input_mail = request.form.get('mail')
    nfile.write("\n")
    nfile.write("\n")
    nfile.close()

    ftp_client = ssh_client.open_sftp()
    ftp_client.put(nfile_name, "/home/" + username + "/slurm-input/" + nfile_name)
    ftp_client.close()
    stdin, stdout, stderr = ssh_client.exec_command("cd ./slurm-input && ./modifiedsubg16 inputMolecule.com")
    job_id = ((stdout.readlines())[-1].split())[-1]
    print(job_id)
    running_subg16_job_mail[job_id] = input_mail

    # todo : check if the calcul as been started properly. if yes return confirmation.html, if not return failed.html
    # todo : create failed.html to tell the user why his request failed
    return render_template("confirmation.html", mail=input_mail)


@app.route("/test")  # example on how to display a matplot. todo : delete after use in result.
def test():
    # fig = create_projection("./output/test.txt")

    # maybe instead of doing the next 4 lines, 2 other option :
    # 1. generate the png of the plot when the mail is sent.
    # (generates lots of trash file, even if the server is shutdown once rebooted the results stay available,
    # no processing time when user open the page)
    # 2. make fig into a global dictionnary and generate the graph when
    # the mail is sent. (no extra file generated, no processing time when page is open, need more memory,
    # results are loss when server is shutdown) <--- CURRENT CHOSEN SOLUTION, found in check_subg16_job_status()
    """png_image = io.BytesIO()
    FigureCanvas(create_projection("./output/test.txt")).print_png(png_image)
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(png_image.getvalue()).decode('utf8')"""

    return render_template("test.html", image=aromaticity_fig_result[0])


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    google_connect()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_subg16_job_status, trigger="interval", seconds=300)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    app.run()
