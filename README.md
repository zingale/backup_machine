# backup_machine

A simple python script that can be run as a cron job to backup
important files and directories to a different filesystem (such as a
different disk in the computer).  The number of copies to store can be
set.  An e-mail is sent when the copy is completed.

The details of the backup are specified in an inputs file (see the 
sample `example.ini`.  This follows the INI format.  In particular,
root directories are given a heading in `[...]` and the list of 
subdirectories and files under the root to be copied are 
listed with the `files = ` and `dirs = ` options.  E.g.:

```
[/home/user]
files = a, t, this, that,
   next, 
   another

dirs = bin/,
       development/,
       stuff/, otherstuff/
```

The global information for the backup is specified in the `[main]`
section as:

```
[main]

root = /raid/backup/auto/
prefix = my-backup-

nstore = 3

email_sender = root@mymachine.org
email_receiver = me@mymachine.org

```

Here `nstore` is the number of simultaneous backups to keep around.
Older ones will be deleted.
