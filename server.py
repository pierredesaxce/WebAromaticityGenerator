from __future__ import print_function

import atexit
import base64
import io
import os
import os.path
import os.path
import sys
import smtplib
import traceback
import paramiko

import email.message
from apscheduler.schedulers.background import BackgroundScheduler
from aromaGraph import create_projection  # may need to implement the method directly instead of having the whole file
from flask import Flask, render_template, request
from flask_mail import Mail, Message

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

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
mail_address = file.readline()

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname="10.184.4.20", username=username, password=password, allow_agent=False, look_for_keys=False)

running_subg16_job_mail = {}
aromaticity_fig_result = {}


def send_email(sender, receiver, subject, body):
    """Send an email using the parameters. The email is sent through the smtp server of Aix-Marseille University
    :param sender: address used to send the email.
    :param receiver: address of the receiver of the email.
    :param subject: subject of the email
    :param body: body of the email
    """
    sender = sender
    receivers = [receiver]

    m = email.message.Message()
    m['From'] = sender
    m['To'] = receiver
    m['Subject'] = subject

    m.set_payload(body)

    try:
        smtpObj = smtplib.SMTP('smtp.univ-amu.fr', 25)
        smtpObj.sendmail(sender, receivers, m.as_string())
        print("Successfully sent email")
    except:
        print(traceback.format_exc())


def check_subg16_job_status():  # THIS NEED TO BE CHANGED but keep the code it will be useful later
    """Check if the subg16 jobs started are done. If a job is finished, retrieve the log file with the result,
    email the user and remove it from the dictionary of job to check. """
    with app.app_context():
        job_done = []
        for job_id in running_subg16_job_mail:
            stdin, stdout, stderr = ssh_client.exec_command("/usr/bin/sacct -p -j " + job_id)
            output = stdout.readlines()
            output_status = (output[-1].split("|"))[-3]
            print(output_status)

            if output_status == "FAILED":

                subject = "Resultat calcul d\'aromaticite"
                body = "Votre calcul d'aromaticite a echoue. Re-essayez et verifiez que le document envoye est correct"
                send_email(mail_address, running_subg16_job_mail[job_id], subject, body)
                job_done.append(job_id)

            elif output_status == "COMPLETED":

                nfile_name = 'inputMolecule.log'
                ftp_client = ssh_client.open_sftp()
                ftp_client.get("/home/" + username + "/slurm-output/" + job_id + "/" + nfile_name,
                               "./output/" + job_id + ".log")
                ftp_client.close()

                png_image = io.BytesIO()
                FigureCanvas(create_projection("./output/test.txt")).print_png(png_image)
                pngImageB64String = "data:image/png;base64,"
                pngImageB64String += base64.b64encode(png_image.getvalue()).decode('utf8')
                aromaticity_fig_result[0] = pngImageB64String
                subject = "Resultat calcul d\'aromaticite"
                body = "Votre calcul d'aromaticite ( id = " + job_id + ") vient de se terminer. Retrouvez les " \
                                                                       "resultats a l'adresse : " \
                                                                       "http://localhost:5000/result/" + job_id
                send_email(mail_address, running_subg16_job_mail[job_id], subject, body)
                job_done.append(job_id)

        for job in job_done:  # remove all job completed
            running_subg16_job_mail.pop(job)


@app.route('/result/<id>')
def show_result(id):
    try:
        output_file = open("./output/" + id + ".log", "r")
        nfile_name = 'inputMolecule.log'
        ftp_client = ssh_client.open_sftp()

        ftp_client.get("/home/" + username + "/slurm-output/" + id + "/" + nfile_name,
                       "./output/" + id + ".log")
        ftp_client.close()

    except:

        return render_template("resultMissing.html")

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
    stdin, stdout, stderr = ssh_client.exec_command(
        "cd ./slurm-input && /share/programs/bin/modifiedsubg16 inputMolecule.com")
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
    # 2. make fig into a global dictionary and generate the graph when
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
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_subg16_job_status, trigger="interval", seconds=60)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    app.run()
