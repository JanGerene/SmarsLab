"""
SMARS Lab
Copyright 2022 Jan Gerene
based on the original SmarsLab of Kevin McAleer
Copyright 2019 Kevin McAleer
3 February 2019
Updated 13 June 2021 
"""

from pathlib import Path
import logging, logging.config


from flask import Flask, render_template, request, jsonify, flash
from markupsafe import Markup
from flask_bootstrap import Bootstrap

from smars import SmarsRobot
import smars as SMARS


logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)

APP = Flask(__name__)
SMARS = SmarsRobot()


@APP.route("/")
def index():
    """ render the main index template """
    return render_template("index.html")


@APP.route("/about")
def about():
    """ returns the about page """
    return render_template("about.html")


@APP.route("/controlapi", methods=['GET', 'POST'])
def controlapi():
    """ control api """
    if request.method == 'POST':
        command = request.values.get('command')
        if command == "up":
            SMARS.walk_forward(steps=10)
        elif command == "down":
            SMARS.walk_backward(steps=10)
        elif command == "left":
            SMARS.turn_left()
        elif command == "right":
            SMARS.turn_right()
        elif command == "stand":
            SMARS.stand()
        elif command == "sit":
            SMARS.sit()
        elif command == "wiggle":
            SMARS.wiggle(1)
        elif command == "clap":
            SMARS.clap(1)
        elif command == "home":
            SMARS.default()
    return "Ok"


def main():
    """ main event loop """
    print("Starting SMARSLab...")
    APP.secret_key = 'development-key'
    APP.host = '0.0.0.0'
    APP.debug = False
    Bootstrap(APP)
    APP.run(host='0.0.0.0')


if __name__ == "__main__":
    main()
