# WebAromaticityGenerator

# Installation

## Getting the code

You can download the code by using this command where you want it to be :

```
git clone https://github.com/pierredesaxce/MolAromaProjection.git
```

### Temporary
After downloading the project, you'll be on the master branch which as not yet been updated, use this command to be on a functioning branch :

```
git checkout preprod
```

## Requirements

You need Python 3 to use this program.

https://www.python.org/downloads/

All the needed dependencies are present in the requirement.txt file. You can download them by using :

```
pip3 install -r requirements.txt
```
in the main folder of the project that you have downloaded.

The user also need to create a file called "token". It should be formatted as follows :

```
usernameOnTheCluster
passswordOnTheCluster
resultMailAddress
```

The "usernameOnTheCluster" and "passswordOnTheCluster" are the one that you use to connect to the cluster and were sent to you when your account on the cluster is created. The address sending them is alta@univ-amu.fr .

The "resultMailAddress" is the email address that will be used to send the result. You can put whatever you want as long as it's a valid email address. ( alta@univ-amu.fr is fine for example).

# Usage

To use it, you just need to go into the project folder and use the following command :

```
python3 server.py
```

It will open create a server on localhost using the port 5000. The user can open the main page of the website by going to http://localhost:5000/ . There, they can upload a .xyz file to receive a log file once the cluster is done processing it. (work in progress, the end goal should be a graph of the aromaticity of the molecule upload.
 
An example page to show how the aromaticity would be displayed, is available on http://localhost:5000/test as soon as one successful response as been sent.
It only works with one file ( output/test.txt ) and is not a fully finished feature rn.