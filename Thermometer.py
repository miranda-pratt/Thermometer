# Raspberry Pi Thermometer Project
# This code is based off / built upon Monk Makes project 4: Thermometer Electronic Starter Kit for Raspberry Pi
# https://monkmakes.com/pi_box_1.html

# How it works:
# The thermistor is an electrical component with a resistance that varies with temperature
# When the temperature is low, resistance is high and vice versa
# To calculate the temperature we need to measure the resistance of the thermistor
# This is achieved using a capacitor, an electrical component that stores charge
# The code records the time it takes for a capacitor to fill when supplied by a current passing through the resistor
# And then uses the Steinhart equation which determines the temperature in Kelvin of a NTC thermistor
# Given the resistance
# The temperature can then be calculated in Celsius and Farenheit
# And output using a Graphical User Interface (GUI)

# Import the necessary packages from Tkinter to create a graphical user interface (GUI)
from tkinter import Tk
from tkinter import Frame
from tkinter import Label
from tkinter import Button
from tkinter import *

# Import RPi.GPIO to use the GPIO pins
import RPi.GPIO as GPIO

# Import time to calculate the time taken for a capacitor to fill with charge
# And import math to calculate logs for the Steinhart equation
import time, math
from functools import partial

from matplotlib.axis import Axis
import matplotlib.pyplot as plt
import numpy as np

# Constants for the program
C = 0.38 # uF - Tweek this value around 0.33 to improve accuracy
R1 = 1000 # Ohms
B = 3800.0 # The thermistor constant - change this for a different thermistor
R0 = 1000.0 # The resistance of the thermistor at 25C - change for different thermistor

# Configure the Pi to use the BCM (Broadcom) pin names, rather than the pin positions
GPIO.setmode(GPIO.BCM)

# Pin names
# The charging pin charges the capacitor through a fixed 1k resistor and the thermistor in series
# The discharging pin discharges the capacitor through a fixed 1k resistor 
CHARGING_PIN = 18
DISCHARGING_PIN = 25

# Set pin numbers for the LEDs
red = 17
yellow = 27
green = 22

# Set up the LEDs as outputs
GPIO.setup(red, GPIO.OUT)
GPIO.setup(yellow, GPIO.OUT)
GPIO.setup(green, GPIO.OUT)

# Readings array
# time_readings_x = np.array([])
# temperature_readings_y = np.array([])
total_time = 0

# Method to discharge the capacitor
# To ensure the capacitor is empty before timing how long it takes for the capacitor to fully charge
# The charging pin is set as an input and the discharging pin as an output
# The output of the discharging pin is set to false to allow the capacitor to discharge
def discharge():
    GPIO.setup(CHARGING_PIN, GPIO.IN)
    GPIO.setup(DISCHARGING_PIN, GPIO.OUT)
    GPIO.output(DISCHARGING_PIN, False)
    time.sleep(0.01)


# Function to calculate the charge time of the capacitor
# The discharging pin is set as an input and the discharging pin as an output
# The output of the charging pin is set to true to allow the capacitor to charge
# The time taken for the voltage on the capacitor to count as a digital input HIGH is calculated
# This is around 1.65V
# The time is the difference between the end and start time and is converted to microseconds
# Return the charge time in microseconds
def charge_time():
    GPIO.setup(DISCHARGING_PIN, GPIO.IN)
    GPIO.setup(CHARGING_PIN, GPIO.OUT)
    GPIO.output(CHARGING_PIN, True)
    start_time = time.time()
    while not GPIO.input(DISCHARGING_PIN):
        pass
    end_time = time.time()
    return (end_time - start_time) * 1000000


# Function to return an analog reading of the time taken for the capacitor to fully charge
# The capactor is discharged before and after the readings
# Return the charge time
def analog_read():
    discharge()
    t = charge_time()
    discharge()
    return t


# Function to convert the time taken to charge the cpacitor into a value of resistance
# To reduce errors, the resistance is taken 10 times and the average is used
def read_resistance():
    n = 10
    total = 0;
    for i in range(0, n):
        total = total + analog_read()
    t = total / float(n)
    T = t * 0.632 * 3.3
    r = (T / C) - R1
    return r


# Function to calculate the temperature based off the resistance
# Uses the Stein-Hart equation
# Returns the temperature in Celsius
def read_temp_c():
    R = read_resistance()
    t0 = 273.15     # 0 deg C in K
    t25 = t0 + 25.0 # 25 deg C in K
    # Steinhart-Hart equation
    inv_T = 1/t25 + 1/B * math.log(R/R0)
    T = (1/inv_T - t0)
    return T


# Function to display the red light (yellow and green off)
def red_light():
    GPIO.output(red, True)
    GPIO.output(yellow, False)
    GPIO.output(green, False)


# Function to display the yellow light (red and green off)
def yellow_light():
    GPIO.output(red, False)
    GPIO.output(yellow, True)
    GPIO.output(green, False)


# Function to display the green light (red and yellow off)
def green_light():
    GPIO.output(red, False)
    GPIO.output(yellow, False)
    GPIO.output(green, True)


# Function to display the different lights based off the temperature in Celsi
# Red light is displayed if temperature is less than 15 degrees or greater than 25 degrees
# Yellow light is displayed if temperature is between 15 and 18 degrees or 22 and 25 degrees
# Green light is displayed if temperature is between 18 and 22 degrees
def display_light(temp_c):
    if (temp_c < 15 or temp_c > 25):
        red_light()
    elif (temp_c >= 15 and temp_c < 18) or (temp_c <= 25 and temp_c > 22):
        yellow_light()
    else:
        green_light()


# Function to get time remaning
# Takes in the paramater time in seconds, subtracts 1 and returns the time remaining
def get_time_remaining(time):
    time_remaining = time - 1
    return time_remaining


# Function to start the timer
# Sets up the timer and then passes to timer2
# inside the app class to finish the timing process
def timer(self, time):
    time_remaining = time
    # Set up Numpy arrays and get the first reading when time = 0
    time_readings_x = np.array([])
    temperature_readings_y = np.array([])
    time_readings_x = np.append(time_readings_x, 0)
    temperature_readings_y = np.append(temperature_readings_y, read_temp_c())

    # Display the time remaining
    time_remaining_str = "{:.2f}".format(time_remaining)
    self.time_remaining_label.configure(text=time_remaining_str)

    # Call the timer2 function after a second to update the clock
    self.master.after(1000, self.timer2(time_remaining + 1, time, 11, time_readings_x, temperature_readings_y))


# Function to plot the graph
# Passes 2 numpy arrays time_readings_x and temperature_readings_y
def plot(time_readings_x, temperature_readings_y):
    fig, ax = plt.subplots()
    ax.plot(time_readings_x, temperature_readings_y)
    ax.xaxis.zoom(-30)
    ax.yaxis.zoom(-100)
    fig.suptitle("Temperature Readings Graph")
    plt.xlabel("Time in seconds")
    plt.ylabel("Temperature in Celsius")
    plt.show()
   

# group together all of the GUI code into a class called App
class App:

    # this function gets called when the app is created
    def __init__(self, master):
        self.master = master
        frame = Frame(master)
        frame.pack()

        # Create the various labels and buttons

        # Instruction labels
        label = Label(frame, text = 'Temperature reader and plotter', font = ("Helvetica", 32))
        label.grid(row=0, column = 0, columnspan = 5, padx = 5, pady = 15)
        label = Label(frame, text = 'Temperatures are recorded at 10 second intervals', font = ("Helvetica", 18))
        label.grid(row=1, column = 0, columnspan = 5, padx = 5, pady = 15)
        label = Label(frame, text = 'Select an option', font = ("Helvetica", 18))
        label.grid(row=2, column = 0, columnspan = 5, padx = 5, pady = 15)

        # Buttons so the various times
        button1 = Button(frame, text = '1 minute', font = ("Helvetica", 18), command = partial(timer, self, 60))
        button1.grid(row=3, column=0, pady = 15)
        button2 = Button(frame, text = '2 minutes', font = ("Helvetica", 18), command = partial(timer,self, 120))
        button2.grid(row=3, column=1, pady = 15)
        button5 = Button(frame, text = '5 minutes', font = ("Helvetica", 18), command = partial(timer,self, 300))
        button5.grid(row=3, column=2, pady = 15)
        button10 = Button(frame, text = '10 minutes', font = ("Helvetica", 18), command = partial(timer,self, 600))
        button10.grid(row=3, column=3, pady = 15)

        # Temperature readings in Celsius and Farenheit and their labels
        label = Label(frame, text='Temp C', font=("Helvetica", 32))
        label.grid(row=4, column=1, columnspan=2)
        self.readingc_label = Label(frame, text='12.34', font=("Helvetica", 18))
        self.readingc_label.grid(row=5, column=1, columnspan=2)
        label = Label(frame, text='Temp F', font=("Helvetica", 32))
        label.grid(row=6, column=1, columnspan=2)
        self.readingf_label = Label(frame, text='12.34', font=("Helvetica", 18))
        self.readingf_label.grid(row=7, column=1, columnspan=2)

        # Main timer label
        label = Label(frame, text='Timer', font=("Helvetica", 32))
        label.grid(row=8, column=1, columnspan=2)
        self.time_remaining_label = Label(frame, text='00:00', font=("Helvetica", 18))
        self.time_remaining_label.grid(row=9, column=1, columnspan=2)

        # Time till next reading label
        label = Label(frame, text = 'Time till next reading', font = ("Helvetica", 32))
        label.grid(row = 10, column=1, columnspan=2)
        self.countdown_label = Label(frame, text = '10', font=("Helvetica", 18))
        self.countdown_label.grid(row=11, column=1, columnspan=2)

        # Call the method to update the temperature readings every second                 
        self.update_readings()


    # Method to update the GUI labels displaying the temperature in Celsius and Farenheit
    def update_readings(self):
        temp_c = read_temp_c()
        temp_f = (temp_c * 1.8) + 32
        display_light(temp_c)
        readingc_str = "{:.2f}".format(temp_c)
        readingf_str = "{:.2f}".format(temp_f)
        self.readingc_label.configure(text=readingc_str)
        self.readingf_label.configure(text=readingf_str)
        self.master.after(1000, self.update_readings)


    # Timer2 method
    # This method is inside the app class to be able to update the GUI readings
    def timer2(self, time_to_countdown, total_time, time_next_reading, time_readings_x, temperature_readings_y):
        # Get the time remaining and update the label
        time_remaining = get_time_remaining(time_to_countdown)
        time_remaining_next_reading = get_time_remaining(time_next_reading)
        time_remaining_next_reading_str = str(time_remaining_next_reading)
        self.countdown_label.configure(text=time_remaining_next_reading_str)
        # Calculate the minutes and seconds remaining
        # Minutes is calculated using integer division
        minutes = time_remaining // 60
        seconds = time_remaining - (minutes * 60)
        # Display the time, if seconds are less than 10 add an extra 0
        # So 1 minute 2 seconds is 1:02 instead of 1:2
        if seconds < 10:
            time_remaining_str = str(minutes) + ":0" + str(seconds)
        else:
            time_remaining_str = str(minutes) + ":" + str(seconds)
        self.time_remaining_label.configure(text=time_remaining_str)

        # When the time remaining for the next reading reaches 0
        # Append to the time and temperature reading numpy arrays
        # This data will be used to plot the graph next
        if time_remaining_next_reading == 0:
            
            time_readings_x = np.append(time_readings_x, (total_time - time_remaining))
            temperature_readings_y = np.append(temperature_readings_y, read_temp_c())

            # Reset time remaining next reading back to 10
            time_remaining_next_reading = 10
            
        # If the total time remaining is 0, call the plot method
        # Pass the numpy arrays as arguments
        # And return (end) the function
        if time_remaining == 0:
            plot(time_readings_x, temperature_readings_y)
            return;

        # Else recall the function after a second, passing all arguments needed
        else:
             self.master.after(1000, self.timer2, time_remaining, total_time, time_remaining_next_reading, time_readings_x, temperature_readings_y)




# Set the GUI running, give the window a title, size and position
root = Tk()
root.wm_title('Thermometer')
app = App(root)
root.geometry("850x800+0+0")
try:
    root.mainloop()
# At the end of the program, cleanup (reset) the GPIO pins
finally:  
    print("Cleaning up")
    GPIO.cleanup()



