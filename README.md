# SMARSLab

This is a reworked version of [Kevin McAleer SMARSLab project](https://github.com/kevinmcaleer/SMARSLab)

* use of Adafruit-circuitpython-PCA9685 library
* use of Adafruit Motor.Servo
* smars library as a module in the project
* setup page removed 
* use of yaml file for configuration

## installation
* ssh into Raspberry Pi zero
* git clone https://github.com/JanGerene/SmarsLab
* cd SmarsLab
* python -m venv venv
* source venv/bin/activate
* pip install -r requirements.txt
* sudo cp smars_lab.service /lib/systemd/system
* sudo systemctl enable smars_lab
* sudo systemctl start smars_lab

contact the server by pointing browser to http://"ip adress smars":5000
