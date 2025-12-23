# app.py
import sys
import threading
from time import sleep
from flask import Flask, render_template, request, redirect

sys.path.append('/home/tom')

from RPLCD.i2c import CharLCD
from motor_driver import DualDCMotorDriver
import manual_mode
import hovering
from auto_mode import AutoMode  # <-- our new library

# Initialize LCD and driver
lcd = CharLCD('PCF8574', 0x27)
lcd.clear()
driver = DualDCMotorDriver(in1_pin=13, in2_pin=19, in3_pin=00, in4_pin=26)

manual = manual_mode.ManualMode(driver, lcd)

app = Flask(__name__)

current_mode = "manual"
auto_thread = None
stop_flag = {'stop': False}  # flag for AutoMode

def update_lcd_mode():
    lcd.clear()
    if current_mode == "manual":
        lcd.write_string("Manual Mode")
    else:
        lcd.write_string("Auto Mode")

@app.route("/", methods=["GET", "POST"])
def index():
    global current_mode, auto_thread, stop_flag

    if request.method == "POST":
        if "mode" in request.form:
            new_mode = request.form["mode"]
            if new_mode != current_mode:
                current_mode = new_mode

                if current_mode == "auto":
                    # Start AutoMode
                    update_lcd_mode()
                    stop_flag['stop'] = False
                    auto_instance = AutoMode(driver, lcd, stop_flag)
                    auto_thread = threading.Thread(target=auto_instance.start)
                    auto_thread.start()

                elif current_mode == "manual":
                    # Stop AutoMode
                    stop_flag['stop'] = True
                    if auto_thread and auto_thread.is_alive():
                        auto_thread.join()
                    driver.stop_all()
                    update_lcd_mode()

            return redirect("/")

        # Handle manual actions
        if current_mode == "manual":
            action = request.form.get("action")
            manual.handle_action(action)

    return render_template("index.html", mode=current_mode)

if __name__ == "__main__":
    update_lcd_mode()
    app.run(host="0.0.0.0", port=5000)


