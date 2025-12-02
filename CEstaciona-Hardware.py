from machine import Pin, ADC, PWM, UART
import time
import json

#Configuración de los pines
SEGMENT_PINS = [Pin(7, Pin.OUT),
                Pin(6, Pin.OUT),
                Pin(5, Pin.OUT),
                Pin(4, Pin.OUT),
                Pin(3, Pin.OUT),
                Pin(2, Pin.OUT),
                Pin(8, Pin.OUT)
                ]

COMMON_PIN = Pin(7, Pin.OUT) #Cátodo común

#Botones
BTN_ENTER = Pin(16, Pin.IN, Pin.PULL_UP)
BTN_EXIT = Pin(17, Pin.IN, Pin.PULL_UP)

LDR1 = ADC(26)
LDR2 = ADC(27)

#LEDs
LED1 = Pin(18, Pin.OUT)
LED2 = Pin(19, Pin.OUT)

#Servomotor
SERVO = PWM(Pin(15))
SERVO.freq(50)

#Comunicacion serial a través de UART(RX, TX, GND)
uart = UART(0, baudrate=115200, tx=Pin(0), rx=pin(1))

#Mapeo display 7 segmentos

DIGIT_MAP = {
    '0': [1, 1, 1, 1, 1, 1, 0], '1': [0, 1, 1, 0, 0, 0, 0],
    '2': [1, 1, 0, 1, 1, 0, 1], '3': [1, 1, 1, 1, 0, 0, 1],
    '4': [0, 1, 1, 0, 0, 1, 1], '5': [1, 0, 1, 1, 0, 1, 1],
    '6': [1, 0, 1, 1, 1, 1, 1], '7': [1, 1, 1, 0, 0, 0, 0],
    '8': [1, 1, 1, 1, 1, 1, 1], '9': [1, 1, 1, 1, 0, 1, 1]
    }

class ParkingHardware:
    def __init__(self, parking_id=1):
        self.parking_id = parking_id
        self.ldr_threshold = 30000
        self.servo_closed = 1500
        self.servo_open = 2500
        self.last_btn_enter = True
        self.last_btn_exit = True
        self.display_mode = "spaces" #spaces o fee
        self.display_value = "2"

        self.setup_servo()
        
    def setup_servo(self):
        self.set_servo_position(self.servo_closed)
    
    
    def set_servo_position(self, us):
        duty = int(us * 65535 / 20000)
        SERVO.duty_u16(duty)
    
    
    def send_data(self, data):
        try:
            data['parking_id'] = self.parking_id
            message = json.dumps(data) + '\n'
            uart.write(message.encode())
        except Exception as e:
            print("Error enviando:", e)
            
    
    
    def receive_data(self):
        try:
            if uart.any():
                data = uart.readline().decode().strip()
                if data:
                    return json.loads(data)
        
        except Exception as e:
            print("Error recibiendo:", e)
            
        return None
    
    
    def update_display(self, value, mode="spaces"):
        self.display_value = str(value)
        self.display_mode = mode
        
        if value in DIGIT_MAP:
            segments = DIGIT_MAP[value]
            for i, state in enumerate(segments):
                SEGMENT_PINS[i].value(state)
                
                
    def read_ldrs(self):
        ldr1_value = LDR1.read_u16()
        ldr2_value = LDR2.read_u16()
        
        ldr1_occupied = ldr1_value > self.ldr_threshold
        ldr2_occupied = ldr2_value > self.ldr_threshold
        
        return ldr1_occupied, ldr2_occupied
    
    def update_leds(self, space1_occupied, space2_occupied):
        LED1.value(not space1_occupied) #LED ON = disponible
        LED2.value(not space2_occupued)
        
    def check_buttons(self):
        btn_enter_state = BTN_ENTER.value()
        btn_exit_state = BTN_EXIT.value()
        
        enter_pressed = not btn_enter_state and self.last_btn_enter
        exit_pressed = not btn_exit_state and self.last_btn_exit
        
        self.last_btn_enter = btn_enter_state
        self.last_btn_exit = btn_exit_state
        
        return enter_pressed, exit_pressed
    
    
    def control_barrier(self, state)
    if state == "open":
        self.set_servo_position(self.servo_open)
        
    else:
        self.set_servo_position(self.servo_closed)
        
    
    def run(self):
        print(f"Parqueo {self.parking_id} iniciado")
        
        last_ldr1 = False
        last_ldr2 = False
        
        while True:
            #Leer sensores y botones
            ldr1_occupied, ldr2_occupied = self.read_ldrs()
            enter_pressed, exit_pressed = self.check_buttons()
            
            #Enviar actualizacion de sensores
            if ldr1_occupied != last_ldr1 or ldr2_occupied != last_ldr2:
                self.send_data({
                    'type': 'sensor_update',
                    'space1_occupied': ldr1_occupied,
                    'space2_occupied': ldr2_occupied
                    })
                
                last_ldr1 = ldr1_occupied
                last_ldr2 = ldr2_occupied
                
            #Enviar eventos de botones físicos
                if enter_pressed:
                    self.send_data({
                        'type': 'button_press',
                        'button': 'enter'
                    })
                if exit_pressed:
                    self.send_data({
                        'type': 'button_press',
                        'button': 'exit'
                        })
                    
                #Actualizar LEDs
                self.update_leds(ldr1_occupied, ldr2_occupied)
                
                #Procesar comandos de la PC
                command = self.receive_data()
                if command and command.get('parking_id') == self.parking_id:
                    self.handle_command(command)
                    
                time.sleep(0.1)
                
    def handle_command(self, command):
        cmd_type = command.get('type')
        
        if cmd_type == 'display_update':
            value = command.get('value', '0')
            mode = command.get('mode', 'spaces')
            self.update_display(value, mode)
            
        elif cmd_type == 'barrier_control':
            state = command.get('state', 'closed')
            self.control_barrier(state)
            
        elif cmd_type == 'led_control':
            state = command.get('state')
            space = command.get('space')
            if space == 1:
                LED1.value(state)
            elif space == 2:
                LED2.value(state)
                
#Configurar ID del parqueo (cambiar por cada Raspberry Pi Pico W)
PARKING_ID = 1

if __name__ == "__main__":
    hardware = ParkingHardware(parking_id=PARKING_ID)
    hardware.run()