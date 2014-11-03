#!/usr/bin/env python

# a simple code to backup critical directories on your machine to a
# separate local disk mounted on that machine.  Several copies are
# kept and an e-mail is sent at the completion.
#
# (use at your own risk...)

import sys
import os
import datetime
import shutil
import smtplib
import ConfigParser
import argparse
from email.mime.text import MIMEText


class Backup:
    """ a simple container class to hold the main information about 
        the backup """
    def __init__(self, root, prefix, nstore, 
                 email_sender, email_receiver):
        
        self.root = root
        self.prefix = prefix
        
        self.nstore = int(nstore)

        self.sender = email_sender
        self.receiver = email_receiver

        dt = datetime.datetime.now()
        self.date = str(dt.replace(second=0, microsecond=0)).replace(" ", "_")


class Log:
    """ a simple logging facility """
    def __init__(self, str=""):
        self.str = str

    def log(self, str):
        print str,
        sys.stdout.flush()
        self.str += str


def report(body, subject, sender, receiver):
    """ send an email """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        smtpObj = smtplib.SMTP('localhost')
        smtpObj.sendmail(sender, receiver, msg.as_string())
    except SMTPException:
        sys.exit("ERROR sending mail")


def do_backup(infile, simulate=False):

    # parse the input file
    cp = ConfigParser.ConfigParser()
    cp.optionxform = str
    cp.read(infile)


    # store the list of files and directories we will backup

    # in each dictionary, the key is the root directory to copy from and the 
    # list it indexes is the list of files/directories under that root to copy
    dirs = {}
    files = {}

    for sec in cp.sections():

        if sec == "main":

            # defaults
            root = "/backup"
            prefix = "my-backup-"
            nstore = 3
            email_sender = "root"
            email_receiver = "root"
        
            for opt in cp.options("main"):
                if opt == "root":
                    root = cp.get(sec, opt)
                elif opt == "prefix":
                    prefix = cp.get(sec, opt)
                elif opt == "nstore":
                    nstore = cp.get(sec, opt)
                elif opt == "email_sender":
                    email_sender = cp.get(sec, opt)
                elif opt == "email_receiver":
                    email_receiver = cp.get(sec, opt)
                else:
                    sys.exit("invalid option in [main]")

                bo = Backup(root, prefix, nstore, 
                            email_sender, email_receiver)
        else:

            for opt in cp.options(sec):
                value = cp.get(sec, opt)

                if opt == "files":
                    flist = [f.strip() for f in value.split(',')]            
                    files[sec] = flist
                    
                if opt == "dirs":
                    dlist = [d.strip() for d in value.split(',')]            
                    dirs[sec] = dlist


    # log the output
    outMsg = "Output from backup-machine.py, inputs file: {}\n".format(infile)

    blog = Log(outMsg)

    # make sure that the output directory exists and if so, get all the
    # subdirectories in it
    try: old_dirs = os.listdir(bo.root)
    except:
        blog.log("destination directory is not readable/doesn't exist\n")
        report(blog.str, subjectFail, bo.sender, bo.receiver)
        sys.exit("directory not readable")


    # how many existing backups are in that directory?
    backup_dirs = []
    for dir in old_dirs:
        if (dir.startswith(bo.prefix) and 
            os.path.isdir(bo.root + '/' + dir)):
            backup_dirs.append(dir)

    backup_dirs.sort()
    backup_dirs.reverse()


    # backup_dirs now contains a list of all the currently stored backups.
    # The most recent backups are at the start of the list.
    print "currently stored backups: "
    for n in range(len(backup_dirs)):
        print backup_dirs[n]


    # get ready for the new backups
    backup_dest = os.path.normpath(bo.root) + '/' + bo.prefix + bo.date
    
    if not simulate:
        try: os.mkdir(backup_dest)
        except: 
            blog.log("error making directory\n")
            report(blog.str, subjectFail, bo.sender, bo.receiver)
            sys.exit("Error making dir")
    else:
        blog.log("mkdir {}\n".format(backup_dest))


    blog.log("writing to: %s\n\n" % (backup_dest) )

    failure = 0

    # backup all the directories
    for root_dir in dirs.keys():
        for d in dirs[root_dir]:

            mydir = os.path.normpath(root_dir) + '/' + d
            if not os.path.isdir(mydir):
                blog.log("WARNING: directory {} does not exist... skipping.\n".format(mydir))
                continue
            else:
                blog.log("copying {}/{} ...\n".format(root_dir, d))

            if not simulate:
                 try: shutil.copytree(mydir,
                                      os.path.normpath(backup_dest) + '/' + d, 
                                      symlinks=True)
                 except:
                     blog.log("ERROR copying\n")
                     blog.log("aborting\n")
                     failure = 1
                     break
    
    blog.log("done with directories\n\n")

    # backup all the files
    for root_dir in files.keys():
        for f in files[root_dir]:

            myfile = os.path.normpath(root_dir) + '/' + f
            if not os.path.isfile(myfile):
                blog.log("WARNING: file {} does not exist... skipping.\n".format(myfile))
                continue
            else:
                blog.log("copying {}/{} ...\n".format(root_dir, f))

            if not simulate:
                try: shutil.copy(myfile,
                                 os.path.normpath(backup_dest) + '/' + f)
                except:
                    blog.log("ERROR copying\n")
                    blog.log("aborting\n")
                    failure = 1
                    break

    blog.log("done with individual files\n\n")


    # if we were successful, then remove any old backups, as necessary
    if not failure:

        # keep in mind that we just stored another backup
        if len(backup_dirs) > bo.nstore-1:
            n = bo.nstore-1

            while n < len(backup_dirs):
                rmDir = bo.root + '/' + backup_dirs[n]

                blog.log("removing old backup: %s\n" % (rmDir) )

                if not simulate:
                    try: shutil.rmtree(rmDir)
                    except:
                        blog.log("ERROR removing %s\n" % (rmDir) )
            
                n += 1

        subject = "summary from backup-machine.py, infile: {}".format(infile)

    else:  
        subject = "ERROR from backup-machine.py, infile: {}".format(infile)


    report(blog.str, subject, bo.sender, bo.receiver)


if __name__ == "__main__":

    # parse any runtime options
    parser = argparse.ArgumentParser()
    parser.add_argument("-s",
                        help="don't do any copies, just output the steps that would be done", 
                        action="store_true")
    parser.add_argument("inputfile", metavar="inputfile", type=str, nargs=1,
                        help="the input file specifying the backup configuration")

    args = parser.parse_args()

    do_backup(args.inputfile[0], simulate=args.s)


