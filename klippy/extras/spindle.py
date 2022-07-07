class Spindle:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.last_power_value = 0
        self.last_power_time = 0.
        self.last_spindle_value = 0.
        self.last_spindle_time = 0.
        
        # Read config
        self.power_pin = config.get('power_pin')
        self.pwm_pin = config.get('pwm_pin')
        self.pwm_time = 1 / float(config.getint('pwm_freq'))
        self.max_rpm = config.getint('max_rpm')
        
        # Create an "pwm" object to handle the spindle rpm
        ppins = self.printer.lookup_object('pins')
        self.spindle_servo = ppins.setup_pin('pwm', self.pwm_pin)
        self.spindle_servo.setup_max_duration(0.)
        self.spindle_servo.setup_cycle_time(self.pwm_time, True)
        self.spindle_servo.setup_start_value(0., 0.)
        self.scale = self.max_rpm
        
        # Create Power On/Off pin
        self.spindle_power = ppins.setup_pin('digital_out', self.power_pin)
        self.spindle_power.setup_max_duration(0.)
        self.spindle_power.shutdown_value = 0.0
        self.spindle_power.setup_start_value(0.0, self.spindle_power.shutdown_value)
        self.last_cycle_time = self.default_cycle_time = 0. # needed for output reschedule

        # Register commands
        gcode = config.get_printer().lookup_object('gcode')
        gcode.register_command("M3", self.cmd_M3)
        gcode.register_command("M5", self.cmd_M5)
        
    def set_speed(self, print_time, value):
        if value == self.last_spindle_value:
            return
        print_time = max(self.last_spindle_time, print_time)
        self.spindle_servo.set_pwm(print_time, value)
        self.last_spindle_time = print_time
        self.last_spindle_value = value

    def set_power(self, print_time, value):
        if value == self.last_power_value:
            return
        print_time = max(self.last_power_time, print_time)
        self.spindle_power.set_digital(print_time, value)
        self.last_power_value = value
        self.last_power_time = print_time
    
    def set_speed_from_command(self, value):
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.register_lookahead_callback((lambda pt:self.set_speed(pt, value)))
    
    def set_power_from_command(self, value):
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.register_lookahead_callback((lambda pt:self.set_power(pt, value)))

    def cmd_M3(self,gcmd):
        val = gcmd.get_int('S', minval=0, maxval=self.scale)
        value = float(val) / self.scale
        self.set_speed_from_command(value)
        self.set_power_from_command(1)
    
    def cmd_M5(self,gcmd):
        self.set_power_from_command(0)
        

def load_config(config):
    return Spindle(config)