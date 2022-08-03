"""
SMARS Lab
Copyright 2022 Jan Gerene
based on the original SmarsLab of Kevin McAleer
Copyright 2019 Kevin McAleer
3 February 2019
Updated 13 June 2021 
"""

from pathlib import Path
import logging


from flask import Flask, render_template, request, jsonify, flash
from markupsafe import Markup
from flask_bootstrap import Bootstrap

from smars import SmarsRobot
import smars as smars


logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)


class CommandHistory:
    _history = []

    @property
    def history(self):
        return self._history

    def append(self, command: str):
        self._history.append(command)

    def clear(self):
        self._history = []

    def get_last_ten(self)->list:
        return self._history[-10:]


DRIVER = smars.do_not_use_pca_driver
app = Flask(__name__)
smars = SmarsRobot()
telemetry = []
command_history = CommandHistory()


@app.route("/")
def index():
    """ render the main index template """
    global telemetry
    telemetry = smars.telemetry
    if DRIVER == True:
        flash(Markup('PCA9685 Driver not loaded.'), 'danger')
    return render_template("index.html")


@app.route("/about")
def about():
    """ returns the about page """
    return render_template("about.html")


@app.route('/metricsapi', methods=['GET', 'POST'])
def metricsapi():
    """ metrics api """
    if request.method == 'POST':
        metric = request.values.get('metric')
        try:
            if metric == "telemetry":
                return jsonify(smars.telemetry)
        except (TypeError):
            logger.debug("jsonify telemetry failed")


@app.route("/controlapi", methods=['GET', 'POST'])
def controlapi():
    """ control api """
    if request.method == 'POST':
        command = request.values.get('command')
        command_history.append(command)
        if command == "up":
            smars.walkforward(steps=10)
        elif command == "down":
            smars.walkbackward(steps=10)
        elif command == "left":
            smars.turnleft()
        elif command == "right":
            smars.turnright()
        elif command == "stand":
            smars.stand()
        elif command == "sit":
            smars.sit()
        elif command == "wiggle":
            smars.wiggle(1)
        elif command == "clap":
            smars.clap(1)
        elif command == "clear_history":
            command_history.clear()
        elif command == "full_history":
            try:
                return jsonify(command_history.history)
            except (TypeError):
                logger.error("could not jsonify full history")
        elif command == "home":
            smars.default()

    return "Ok"


def shutdown_server():
    """ shutsdown the SMARSLab web server """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/shutdown')
def shutdown():
    """ requests the web server shutsdown """
    shutdown_server()
    return 'Server shutting down... Done.'


@app.route('/background_process')
def background_process():
    """ return dynamic data to JQuery """
    try:
        lang = request.args.get('proglang')
        if str(lang).lower() == 'python':
            return jsonify(result='you are wise')
        else:
            return jsonify(result="try again")
    except Exception as error:
        logger.error(error)    
    return jsonify(result="There was an error")


@app.route('/telemetry')
def get_telemetry():
    """ return the current telemetry in JSON format """
    return jsonify(telemetry)


@app.route('/commandhistory', methods=['POST', 'GET'])
def get_command_history():
    """ returns the command history """
    if request.method == 'POST':
        listtype = request.values.get('listtype')
        if listtype == "top10":
            try:
                return jsonify(command_history.get_last_ten())
            except (TypeError) as e:
                logger.debug(e)
                logger.debug("could not jsonify last 10 commands ")
        else:
            try:
                return jsonify(command_history.history)
            except (TypeError) as e:
                logger.debug(e)
                logger.debug("could not jsonify command history " + e)
        return jsonify("command history failed")



@app.route('/setup')
def setup():
    """ The setup wizard screen """
    if DRIVER is True:
        flash(Markup('Driver not loaded'), 'danger')

    return render_template("setup.html")


@app.route('/test', methods=['GET', 'POST'])
def test():
    """ Tests a limb passed to it by a channel number """
    return render_template("setup.html")


def main():
    """ main event loop """
    print("Starting SMARSLab...")
    app.secret_key = 'development-key'
    app.host = '0.0.0.0'
    app.debug = True
    Bootstrap(app)
    app.run(host='0.0.0.0')


if __name__ == "__main__":
    main()
