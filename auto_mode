import sys
import time
from gpiozero import Button
sys.path.append("/home/tom")

from motor_driver import DualDCMotorDriver
from huskylib import HuskyLensLibrary
from ev3motor import EV3Motor
import gyro
import hovering

class AutoMode:
    def __init__(self, driver, lcd, stop_flag_dict):
        self.driver = driver
        self.lcd = lcd
        self.stop_flag_dict = stop_flag_dict
        self.running = False

        self.target_x = 160
        self.deadzone = 40
        self.min_speed = 100
        self.max_speed = 100

        self.gun_button = Button(4)
        self.gun_motor = EV3Motor(8, 25, 22, 10)
        self.gun_motor.reset_encoder()
        self.gun_initialized = False
        self.gun_active = False 

        self.hl = None
        self.gyro_available = False
        self.offset_z = 0
        self.current_lcd_text = ""

        self.init_huskylens()
        self.init_gyro()

    def init_huskylens(self):
        try:
            self.hl = HuskyLensLibrary("I2C", "", address=0x32)
            self.hl.algorthim("ALGORITHM_FACE_RECOGNITION")
            print("HuskyLens initialized")
        except Exception as e:
            print(f"! Camera error: {e}")

    def init_gyro(self):
        try:
            if gyro.mpu_init():
                print("Calibrating gyro...")
                self.offset_z = gyro.calibrate_gyro()
                self.gyro_available = True
        except:
            self.gyro_available = False

    def get_face(self):
        try:
            result = self.hl.blocks()
            if hasattr(result, 'x'):
                return result
            elif result and len(result) > 0:
                return result[0]
        except:
            return None
        return None

    def calculate_movement(self, face):
        error = self.target_x - face.x
        if abs(error) <= self.deadzone:
            return 0, 0

        gyro_factor = 1.0
        if self.gyro_available:
            try:
                raw_gz = gyro.robust_read(0x47)
                gz = (raw_gz / 65.5) - self.offset_z
                gyro_factor = max(0.5, 1.0 - abs(gz)/150.0)
            except:
                pass

        turn_speed = max(self.min_speed, min(self.max_speed, abs(error)/2)) * gyro_factor
        if error < 0:
            left, right = 0, turn_speed
        else:
            left, right = turn_speed, 0

        return max(0, min(100, left)), max(0, min(100, right))

    def initialize_gun_position(self):
        try:
            print("Auto mode started - moving gun down")
            while not self.gun_button.is_pressed and self.running:
                self.gun_motor.goto_degrees(200, kp=2.0, ki=0, kd=0, timeout=1)
                time.sleep(0.05)
            if self.running:
                print("Gun Home Position Reached.")
                self.gun_initialized = True
                self.gun_active = False 
        except Exception as e:
            print(f"Error initializing gun: {e}")

    def gun_sequence(self):
        try:
            if self.gun_initialized:
                print("Target Locked - Raising gun")
                self.gun_motor.goto_degrees(2000, kp=2, ki=0, kd=0, timeout=2)
        except Exception as e:
            print(f"Error in gun sequence: {e}")

    def reset_gun_position(self):
        try:
            if not self.gun_initialized: return
            print("Resetting gun to search position...")
            self.gun_motor.goto_degrees(-200, kp=2, ki=0, kd=0, timeout=2)
            while not self.gun_button.is_pressed and self.running:
                self.gun_motor.goto_degrees(-200, kp=5, ki=0.1, kd=0, timeout=0.2)
                time.sleep(0.01)
            self.gun_active = False
        except Exception as e:
            print(f"Error resetting gun: {e}")

    def update_lcd(self, text):
        if text != self.current_lcd_text:
            self.lcd.clear()
            self.lcd.write_string(text)
            self.current_lcd_text = text

    def auto_worker(self):
        last_face_time = time.time()
        hover_delay = 4.0      # זמן תחילת חיפוש אקטיבי (נסיעה)
        gun_down_delay = 2.0   # זמן המתנה לפני הורדת הרובה
        was_tracking = False

        # התחלה: רובה למטה
        self.initialize_gun_position()

        while self.running:
            face = self.get_face()
            now = time.time()

            if face:
                last_face_time = now # עדכון זמן אחרון שראינו פנים
                
                if not was_tracking:
                    self.driver.stop_all()
                    self.update_lcd("Target Locked")
                    print("\n[AUTO] Target Found! Raising Gun.")
                    was_tracking = True
                    
                    if self.gun_initialized and not self.gun_active:
                        self.gun_sequence()
                        self.gun_active = True

                # תנועת מעקב
                left, right = self.calculate_movement(face)
                self.driver.move_both(left, right)

            else:
                # --- מצב שבו לא רואים פנים ---
                time_since_last_face = now - last_face_time

                # עצירת המנועים אם הפנים נעלמו ליותר מ-0.2 שניות
                if was_tracking and time_since_last_face > 0.2:
                    self.driver.stop_all()

                # האם עבר מספיק זמן כדי להוריד את הרובה?
                if was_tracking and time_since_last_face > gun_down_delay:
                    print("\n[AUTO] Confirmed Lost - Lowering Gun")
                    self.update_lcd("Searching...")
                    was_tracking = False
                    
                    if self.gun_initialized and self.gun_active:
                        self.reset_gun_position()
                    
                    # איפוס ה-hovering לקראת חיפוש
                    hovering.reset_hovering(self.driver, forward_duration=5.0)

                # כניסה למצב הוברינג (חיפוש בנסיעה)
                if time_since_last_face > hover_delay:
                    hovering.hover_step(self.driver)

            time.sleep(0.01) 

    def start(self):
        self.running = True
        self.auto_worker()

    def stop(self):
        self.running = False
        self.driver.stop_all()
        if self.gun_initialized:
            self.reset_gun_position()
        self.gun_motor.stop()
        self.update_lcd("Manual Mode")
