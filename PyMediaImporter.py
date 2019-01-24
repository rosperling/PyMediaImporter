"""
PyMediaImporter is a helper script for importing photos and videos into a
predefined directory structure based on creation date and/or EXIF information

Written by Robert Sperling
Released under the GPL 3.0
"""

from Tkinter import *
from shutil import copyfile
import os, datetime, StringIO, subprocess, shlex
import tkFileDialog
import re

# encoding schemes for directories if you like to use other keywords than
# YYYY, MM or DD change the newpath assignment with replace accordingly
schemes = [
    ("YYYY/YYYYMMDD",1),
    ("YYYYMMDD",2),
    ("YYYY/MMYY",3),
    ("YYYY/YYYY-MM-DD",4),
    ("DD.MM.YYYY",5),
    ("Eigenes Muster",6)
]

master = Tk()

# Selection of encoding scheme for directories
scheme = IntVar()
scheme.set(1)

# extraction method
useexif = IntVar()
useexif.set(1)

# helper functions
def get_creation_date(filename):
    # get creation time - as long as we do not look into the EXIF information this should be sufficient
    t = os.path.getctime(filename)
    # extract out dates
    return (str(datetime.datetime.fromtimestamp(t).year), "%02d" % datetime.datetime.fromtimestamp(t).month, "%02d" % datetime.datetime.fromtimestamp(t).day)

def get_exif_creation_date(filename):
    ## call date command ##
    p = subprocess.Popen("mdls -name kMDItemContentCreationDate %s" % filename, stdout=subprocess.PIPE, shell=True)
    ## Talk with date command i.e. read data from stdout and stderr. Store this info in tuple ##
    ## Interact with process: Send data to stdin. Read data from stdout and stderr, until end-of-file is reached.  ##
    ## Wait for process to terminate. The optional input argument should be a string to be sent to the child process, ##
    ## or None, if no data should be sent to the child.
    (output, err) = p.communicate()
    ## Wait for date to terminate. Get return returncode ##
    p_status = p.wait()
    return output.split(" ")[2].split("-")

def get_exif_property(filename, myproperty):
    args = "sips -g %s %s" % (myproperty.replace("%", ""), filename)
    #print "args: %s" % args
    p = subprocess.Popen(args , stdout=subprocess.PIPE, shell=True)
    ## Interact with process: Send data to stdin. Read data from stdout and stderr, until end-of-file is reached.  ##
    ## Wait for process to terminate. The optional input argument should be a string to be sent to the child process, ##
    ## or None, if no data should be sent to the child.
    (output, err) = p.communicate()
    ## Wait for mdls to terminate. Get return returncode ##
    p_status = p.wait()
    output = output.splitlines()[1].split(":")[1].replace(" ","")
    #print "output: <%s>" % output
    return output
 
def choose_inputpath():
    options = {}
    options['initialdir'] = e1.get()
    options['title'] = "Quellpfad angeben"
    options['mustexist'] = False
    newpath = tkFileDialog.askdirectory(**options);
    if len(newpath) > 0:
        e1.delete(0,END)
        e1.insert(0,newpath)

def choose_outputpath():
    options = {}
    options['initialdir'] = e2.get()
    options['title'] = "Zielpfad angeben"
    options['mustexist'] = False
    newpath = tkFileDialog.askdirectory(**options);
    if len(newpath) > 0:
        e2.delete(0,END)
        e2.insert(0,newpath)

def help_dialog():
    print get_exif_property("Fernweh.jpeg", "kMDItemAcquisitionModel")

# import all photos from e1 to e2 using directory scheme v 
def import_photos():

    # take care of possible user directory name indicated by ~/
    inpath = e1.get()
    if inpath.find("~") >= 0:
        inpath = os.path.expanduser(inpath)    

    # take care of possible user directory name indicated by ~/
    outpath = e2.get()
    if outpath.find("~") >= 0:
        outpath = os.path.expanduser(outpath)
        
    #print("Importing photos from: %s\nImporting photos to: %s" % (inpath, outpath))
    for dirname, dirnames, filenames in os.walk(inpath):
        # print path to all subdirectories first.
        # for subdirname in dirnames:
        #    print("found directory %s" % os.path.join(dirname, subdirname))

        # dive into directories and walk through filenames
        for filename in filenames:
            # extract out dates
            if useexif == 1:
                (year, month, day) = get_exif_creation_date(os.path.join(dirname, filename))
            else:
                (year, month, day) = get_creation_date(os.path.join(dirname, filename))

            if str(schemes[scheme.get()-1][0]) == "Eigenes Muster":
                newpath = e3.get().replace('YYYY', str(year)).replace('MM', month).replace('DD', day)
            else:
                newpath = schemes[scheme.get()-1][0].replace('YYYY', str(year)).replace('MM', month).replace('DD', day)

            # currently handling different file types makes no real sense - it will get usefull if we look deeper into the EXIF infos
            if filename[0] == '.':
                continue
            if filename.find(".JPG") >= 1 or filename.find(".CR2") >= 1:
                # print ("JPEG: %s" % os.path.join(outpath, newpath, filename))
                # path construction - change this if you add new directory scheme types
                # unfortunately we have to use different extraction methods for each filetype here
                if str(schemes[scheme.get()-1][0]) == "Eigenes Muster":
                    regexp = re.compile(r'%[a-zA-Z]+%')
                    while regexp.search(newpath):
                        m = regexp.search(newpath)
                        newpath = re.sub(m.group(0), get_exif_property(os.path.join(dirname, filename),m.group(0)),newpath)
                        #print "newpath: <%s>" % newpath
            elif filename.find(".MOV") >= 1:
                print("MOV: " + os.path.join(outpath, newpath, filename))
            elif filename.find(".MP4") >= 1:
                print("MP4: " + os.path.join(outpath, newpath, filename))        
            else:
                print("skipping %s, unknown type" % os.path.join(dirname, filename))
                continue
                
            # create all nessessary directories to store the files later
            # print ("path to create; %s" % os.path.join(outpath, newpath))
            if not os.path.exists(os.path.join(outpath, newpath)):
                os.makedirs(os.path.join(outpath, newpath))
            copyfile(os.path.join(dirname, filename), os.path.join(outpath, newpath, filename))            

    # remove trash and exit after all work is done
    e1.delete(0,END)
    e2.delete(0,END)
    exit()

master.title("MacPhotoImporter")

# make the master resizable
Grid.rowconfigure(master, 0, weight=1)
Grid.columnconfigure(master, 0, weight=1)

#Create & Configure frame to fill the master
frame=Frame(master)
frame.grid(row=0, column=0, sticky=N+S+E+W)

# labels for our dialog - this should be done via i18n functions - TODO
Label(frame, text="Quellverzeichnis").grid(row=0, sticky=N+W)
Label(frame, text="Zielverzeichnis").grid(row=1, sticky=N+W)

# Configure Input path text field with file chooser
e1 = Entry(frame)
e1.insert(20,"/Volumes/EOS_DIGITAL/DCIM/")
e1.grid(row=0, column=1, sticky=N+E+W)
infilebutton = Button(frame, text="V", command=choose_inputpath)
infilebutton.grid(row=0, column=2, sticky=N+E+W)

e2 = Entry(frame)
e2.insert(20,"~/Pictures/Importer")
e2.grid(row=1, column=1, sticky=N+E+W)
outfilebutton = Button(frame, text="V", command=choose_outputpath)
outfilebutton.grid(row=1, column=2, sticky=N+E+W)

# choose between exif and file creation date mode
Checkbutton(frame, text="Nutze EXIF-Datum", variable=useexif).grid(row=2, sticky=N+W)
Grid.rowconfigure(frame, 1, weight=2)

# add radiobuttons with our directory schemes
Label(frame, text="Verzeichnisschema").grid(row=3, sticky=N+W)
for txt, val in schemes:
    Radiobutton(frame, text=txt, padx = 20, variable=scheme, value=val).grid(row=2 + val, column=1, sticky=N+W, pady=4)

e3 = Entry(frame)
e3.grid(row=3 + val, column=1, sticky=N+E+W)
helpbutton = Button(frame, text="?", command=help_dialog)
helpbutton.grid(row=3 + val, column=2, sticky=N+E+W)

# finally add our magic buttons that do the work
Button(frame, text='Ende', command=master.quit).grid(row=4 + val, column=0, sticky=S+W, pady=4)
Button(frame, text='Importieren', command=import_photos).grid(row=4 + val, column=1, sticky=S+E, pady=4)

Grid.rowconfigure(frame, 2, weight=1)

# make the text entry fields resizeable
Grid.columnconfigure(frame, 1, weight=1)

# liftoff
mainloop( )