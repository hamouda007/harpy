#!/usr/bin/env python

"""harpy.py: Module Description ..."""

__author__ = "Minos Galanakis"
__license__ = "LGPL"
__version__ = "0.0.1"
__email__ = "minos197@gmail.com"
__project__ = "harpy"
__date__ = "25-09-2015"

from flask import Flask, render_template, request, url_for, copy_current_request_context ,redirect
from flask.ext.socketio import SocketIO, emit

from threading import Thread, Event

from time import sleep
import datetime


from formatutils import *
from updater import PageUpdater
from arp import ARPHandler

#Test DataSet
# TODO remove it when testing is complete
from test_dataset import get_data
data_d = get_data()

# Flask App config
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
app.config['SERVER_NAME']='localhost:7777'

# Wrap the app to a SocketIO for async tasks
socketio = SocketIO(app)

# Start the Background monitor thread
arph = ARPHandler()
arph.start()

# User Gui thread
gui = Thread()


#################
## Flask Routes #
#################

@app.route("/")
def main():
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    templateData = {
        'title': 'Harpy!',
        'time': timeString
    }
    return render_template('index.html', **templateData)

@app.route('/add')
def add():
  # Create the buttons
  
  data = gen_radio_buttons("ipsel", "Select the device  you wish to bind", arph.get_table())
  return render_template('form_add.html', dyndata = data)

@app.route('/disable')
def disable():
  """ Stop the allert thread"""
 
  if arph.isAlive():
    arph.stop()
  return redirect("/", code=302)
    
@app.route('/enable')
def enable():
  """ Start the allert thread """

  # TODO make it maintain the table, using config or deepcopy
  try: del(arph)
  except UnboundLocalError: pass
  arph = ARPHandler()
  arph.start()
  return redirect("/", code=302)

@app.route('/form/', methods=['POST'])
def form():
    alias     = request.form['alias']
    if not len(alias): alias = "N.A"
    color     = request.form['color']
    ipsel = request.form['ipsel']
    
    arp_entry = gui.get_table()[ipsel]
    gui.clear_color(color)
    arp_entry['color'] = color
    if len(alias): arp_entry['alias'] = alias

    return render_template(
        'form_action.html',
        alias = alias,
        color = color,
        maddr = arp_entry["mac"])

@socketio.on('connect', namespace='/autoreload')
def client_connect():

    global gui
    print('Client connected')

    # Only start if it its not already started
    if not gui.isAlive():
        print "Starting Thread"
        gui = PageUpdater(socketio,arph.get_table())
        gui.start()

@socketio.on('disconnect', namespace='/autoreload')
def client_disconnect():
    print('Client disconnected')
    gui.stop()

if __name__ == "__main__":
    socketio.run(app)
