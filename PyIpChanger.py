#!/usr/bin/python2.7

import os
import sys
import subprocess
from PyQt4.QtCore import * 
from PyQt4.QtGui import * 
import socket
import struct
import random
import string
import signal

OT_RSA = '109120132967399429278860960508995541528237502902798129123468757937266291492576446330739696001110603907230888610072655818825358503429057592827629436413108566029093628212635953836686562675849720620786279431090218017681061521755056710823876476444260558147179707119674283982419152118103759076030616683978566631413'

def padStr(string, length):
    strLen = len(string)
    for x in xrange(length-strLen):
        string += "\x00"
        
    return string

def quit(*a):
    QApplication.quit()
    
class IpChanger(QWidget): 
    def __init__(self, *args): 
        QWidget.__init__(self, *args) 
 
        # Set title
        self.setWindowTitle("PyIpChanger v1.2")
        
        # create objects
        label = QLabel(self.tr("Browse to your Tibia."))
        labelHostname = QLabel(self.tr("IP Address or Hostname"))
        labelPort = QLabel(self.tr("Port"))
        label3 = QLabel(self.tr("Messages"))
        credit = QLabel(self.tr('Developed by Stian. Lisenced under GPL.'))
        
        self.settings = QSettings("PyIpChanger", QSettings.NativeFormat)
        self.le = QLineEdit()
        self.port = QLineEdit()
        self.port.setMaxLength(4)
        self.port.setValidator(QIntValidator(20, 0xFFFF, self))
        self.pathToExe = QLineEdit()
        self.pathButton = QPushButton("Browse for Tibia")
        self.startButton = QPushButton("Start!")
        self.te = QTextEdit()
        self.te.setFixedHeight(50)
        self.thread = None
        self.windowsClient = False
        
        # Restore settings
        if self.settings.contains("IP"):
            self.le.setText(str("beer.servegame.com"))
            
        if self.settings.contains("PATH"):
            self.pathToExe.setText(str("./Tibia"))

        if self.settings.contains("PORT"):
            self.port.setText(str(self.settings.value("PORT").toPyObject()))
        else:
            # Default port
            self.port.setText("7171")
            
        self.running = False
        
        # layout
        layout = QGridLayout(self)
        layout.addWidget(label, 0, 0)
        layout.addWidget(self.pathToExe, 1, 0)
        # layout.addWidget(self.pathButton, 1, 1)
        layout.addWidget(labelHostname, 2, 0)
        layout.addWidget(labelPort, 2, 1)
        layout.addWidget(self.le, 3, 0)
        layout.addWidget(self.port, 3, 1)
        layout.addWidget(label3, 4, 0)
        layout.addWidget(self.te, 5, 0)
        layout.addWidget(self.startButton, 5, 1)
        layout.addWidget(credit, 6,0, 1, 3)
        self.setLayout(layout) 

        # create connections
        self.connect(self.le, SIGNAL("returnPressed(void)"),
                     self.run)
                     
        self.connect(self.startButton, SIGNAL("clicked()"),
                     self.run) 
                     
        self.connect(self.pathButton, SIGNAL("clicked()"),
                     self.browse)

    def run(self):
        # Allow Hostnames longer than 17 chars by resolving the IP:
        text = str(self.le.text())
        if len(text) > 17:
            try:
                ip = socket.gethostbyname(text)
                if ip != text:
                    self.te.append("'%s' resolved to '%s'" % (text, ip))
                    text = ip
            except:
                self.te.append("'%s' could not be resolved! Is it a valid IP/Hostname?" % (text))
                return
                
        # String object, and the directory
        path = str(self.pathToExe.text())
        directory = os.path.dirname(path)
        
        # This might give a open error if the path is wrong
        try:
            tibia = open(path, "r+b")
        except:
            self.te.append("Error: Unable to open %s" % path)
            return
            
        # This might be NULL if we don't have read access
        data = tibia.read()
        if data == None:
            self.te.append("Error: Unable to read file. Do you have access to it?")
            return

        # Windows or linux client?
        self.windowsClient = ".exe" in path.lower()
        
        # Fix ip
        data = self.fixer(data, text)
        
        if data == None:
            return
            
        # Write temp file.
        tmpFileName = directory + "/" + self.randomFileName()
        tmpFile = open(tmpFileName, "wb")
        tmpFile.write(data)
        
        tmpFile.close()
        
        # Change directory, it will load resources from here.
        os.chdir(directory)
        
        # Save IP for later
        self.settings.setValue("IP", text)
        
        # Save Port for later
        self.settings.setValue("PORT", str(self.port.text()))
        
        self.te.append("Running...")
        
        # Chmod on Linux
        if sys.platform == "linux2":
            try:
                os.chmod(tmpFileName, 0777)
            except:
                pass
        
        # Mark the file as hidden on Windows
        else:
            try:
                subprocess.call(["attrib", "+h", tmpFileName], shell=False)
            except:
                pass

        # Are we opening a .exe on Linux? Then we can use WINE :)
        if sys.platform == "linux2" and self.windowsClient:
            self._run(["wine", tmpFileName], tmpFileName)
        else:    
            self._run(tmpFileName)
        
    def browse(self):
        # Open file dialog
        filename = QFileDialog.getOpenFileName(self, "Open Tibia", self.pathToExe.text())
        
        # Ignore if the user didn't specify a file.
        if not filename:
            return
            
        # Set the field
        self.pathToExe.setText(filename)
        
        # Save for later
        self.settings.setValue("PATH", filename)
        
    def _run(self, command, file=None):
        if file == None:
            file = command
            
        class Thread(QThread):
            def run(self):
                self.emit( SIGNAL('_running()'))
                
                # Start
                self.p = subprocess.call(self.command, shell=False)
                os.remove(self.file) 
                
                self.emit( SIGNAL('_notRunning()'))
       
        # Set thread parameters
        self.thread = Thread()
        self.thread.file = file
        self.thread.command = command
        
        # Bind signals (threadsafe)
        self.connect(self.thread, SIGNAL('_running()'), self._running)
        self.connect(self.thread, SIGNAL('_notRunning()'), self._notRunning)
        
        # Start thread
        self.thread.start()

    def _running(self):
        self.startButton.setDisabled(True)
        self.startButton.setText("Tibia is running...")  
        
    def _notRunning(self):
        self.startButton.setEnabled(True)
        self.startButton.setText("Start!")        
    
    def randomFileName(self):
        return ".__" + (''.join(random.choice(string.letters) for i in xrange(14))) + ".exe"
        
    def fixer(self, data, ip):
        # First RSA key
        base = data.find('1321277432058722840622950990822933849527763264961655079678763')
        if base == -1:
            # Pre 8.61
            base = data.find('124710459426827943004376449897985582167801707960697037164044904')
        
        if base == -1:
            self.te.append("WARNING: Couldn't fix the RSA key!")
        else:    
            # Replace
            data = data[:base] + padStr(OT_RSA, 310) + data[base+310:]
        
        # Then it's the IP
        base = data.find("login01.tibia.com")
        if base == -1:
            # Pre 9.1
            base = data.find("tibia05.cipsoft.com")
            if base == -1:
                # Even older?
                base = data.find("tibia2.cipsoft.com")
                
        if base == -1:
            self.te.append("ERROR: Couldn't fix the IP address!")
            return
        
        
        basePadding = data.find("login02.tibia.com") - data.find("login01.tibia.com") # Required for post-9.44 clients. Atleast on Linux.
        if basePadding < 3:
            basePadding = 20 

        data = data[:base] + (padStr(ip, basePadding) * 10) + data[base+(basePadding * 10):]
        
        # Then the ports:
        # On Linux this is always before the IPs, while on Windows, I believe it's after
        # Either way, we use search :)
        
        base = data.find("\x03\x1c\x00\x00", base-300, base+300)
        try:
            port = int(self.port.text())
            if port and port != 7171:
                if base == -1:
                    self.te.append("ERROR: Couldn't fix the Port!")
                    return
                    
                for x in xrange(10):
                    data = data[:base] + struct.pack("<H", port) + data[base+2:]
                    base += 8
        except ValueError:
            self.te.append("Invalid port!")
        
        # Then make an attempt on the multi client.
        # TODO: Linux clients!
        # Early models
        if self.windowsClient:
            base = data.find('\x84\xC0\x75\x52\x68')
            if base == -1:
                # 8.6+ i think.
                base = data.find('\xC3\x83\xF8\x01\x7E\x0E\x6A')
                if base == -1:
                    # 9.1+
                    base = data.find('\x70\xF4\xFF\xFF\x00\x75\x40')
                    if base != -1:
                        base += 5
                else:
                    base += 4
            else:
                base += 2
           
            if base:
                data = data[:base] + "\xEB" + data[base+1:]
            else:
                self.te.append("WARNING: Couldn't apply MC patch!")

        return data
        
if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit)
    
    app = QApplication(sys.argv) 
    w = IpChanger() 
    w.show() 
    sys.exit(app.exec_())
