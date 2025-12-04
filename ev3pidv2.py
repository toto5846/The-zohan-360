from gpiozero import Motor, Button
import time

class EV3Motor:
    def __init__(self, encoder1_pin, encoder2_pin, in1_pin, in2_pin):
        self.motor = Motor(forward=in1_pin, backward=in2_pin, pwm=True)
        self.encoder1 = Button(encoder1_pin)
        self.encoder2 = Button(encoder2_pin)

        self.encoder1.when_pressed = self.encoder_callback
        self.encoder1.when_released = self.encoder_callback

        self.degrees = 0

        # PID variables
        self.last_error = 0
        self.integral = 0
        self.last_time = None

    def encoder_callback(self):
        a = self.encoder1.value
        b = self.encoder2.value
        if a == b:
            self.degrees += 1
        else:
            self.degrees -= 1

    def motgo(self, speed):
        speed = max(-100, min(100, speed))
        min_pwm = 0.1 
        pwm_value = min_pwm + (1 - min_pwm) * abs(speed) / 100.0

        if speed > 0:
            self.motor.forward(pwm_value)
        elif speed < 0:
            self.motor.backward(pwm_value)
        else:
            self.motor.stop()

    def goto_degrees(self, clicks_to_move, kp=0.5, ki=0.0, kd=0.0, timeout=10):
        start_pos = self.degrees
        target_pos = start_pos + clicks_to_move
        self.last_time = time.time()
        self.integral = 0
        self.last_error = 0

        max_speed = 100
        min_speed = 8 

        print(f"Moving motor {clicks_to_move} clicks with PID: kp={kp}, ki={ki}, kd={kd}")

        print("Time(s) |   SP  |   PV  |  Error |  Speed")
        print("---------------------------------------")

        while True:
            current_time = time.time()
            dt = current_time - self.last_time
            if dt == 0:
                dt = 0.01

            error = target_pos - self.degrees

           
            if abs(error) < 5:
                break

           
            self.integral += error * dt
            derivative = (error - self.last_error) / dt

            speed = kp * error + ki * self.integral + kd * derivative

    
            if speed > max_speed:
                speed = max_speed
            elif speed < -max_speed:
                speed = -max_speed

        
            if 0 < abs(speed) < min_speed:
                speed = min_speed if speed > 0 else -min_speed

            self.motgo(speed)

            elapsed = current_time - self.last_time
            print(f"{elapsed:6.2f} | {target_pos:5.1f} | {self.degrees:5} | {error:6.1f} | {speed:6.1f}")

            self.last_error = error
            self.last_time = current_time

            time.sleep(0.02)

        self.motgo(0)
        print("Movement complete.")

    def reset_encoder(self):
        self.degrees = 0

    def stop(self):
        self.motgo(0)
