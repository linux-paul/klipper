import time
from . import probe

class Mpcnc:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.config = config

        # other data
        self.step_dist = {"x":0.0,"y":0.0,"z":0.0}

        # Read config
        self.wzl_pin = config.get('wzl_pin')
        self.wzl_offset = config.getfloat('wzl_offset',0.)
        self.wzl_retract = config.getfloat('wzl_retract',0.)
        self.wzl_cust_homing = config.getboolean('wzl_cust_homing',False)
        if self.wzl_cust_homing:
            self.wzl_homing_speed = config.getfloat('wzl_homing_speed',0.)
            self.wzl_second_homing_speed = config.getfloat('wzl_second_homing_speed',0.)
            self.wzl_homing_retract_dist = config.getfloat('wzl_homing_retract_dist',0.)
            self.homing_data = {"speed":self.wzl_homing_speed,
                                "2_speed":self.wzl_second_homing_speed,
                                "dist":self.wzl_homing_retract_dist,
                                "dir":False,
                                "max":0.0,
                                'min':0.0
                                }
        self.tp_used = config.getint("tp_used",0)
        self.tp_height = config.getfloat("tp_height",0.)
        self.park_x = config.getint("park_pos_x",0)
        self.park_y = config.getint("park_pos_y",0)
        
        # Create Endstop
        endstop_pin = self.wzl_pin
        ppins = self.printer.lookup_object('pins')
        mcu_endstop = ppins.setup_pin('endstop', endstop_pin)
        query_endstops = self.printer.load_object(config, 'query_endstops')
        query_endstops.register_endstop(mcu_endstop, 'wzl')
        self.mapstop = mcu_endstop
        
        # Register event: om "mcu_identify" from klippy.py run def handle_mcu_identify
        self.printer.register_event_handler('klippy:mcu_identify', self._handle_mcu_identify)
                       
        # Register CMD
        self.gcode = config.get_printer().lookup_object('gcode')
        self.gcode.register_command("HOME_WZL", self.cmd_HOME_WZL)
        self.gcode.register_command("SET_MESHCONFIG", self.cmd_SET_MESHCONFIG)
        self.gcode.register_command("CREATE_MESH", self.cmd_CREATE_MESH)
        self.gcode.register_command("MOVE_CNC", self.cmd_MOVE_CNC)
        self.gcode.register_command("ENABLE_TP", self.cmd_ENABLE_TP)
        self.gcode.register_command("DISABLE_TP", self.cmd_DISABLE_TP)
        self.gcode.register_command("PARK_TOOL", self.cmd_PARK_TOOL)
  
    def _flip_homing_data(self):
        if self.orig_homing["max"] > 0 :
            self.homing_data["min"] = self.orig_homing["nax"] *-1
        else:
            self.homing_data["max"] = self.orig_homing["min"] *-1
        self.rail.change_homing_data(self.homing_data)

    def _flip_endstop(self):
        oldstop = self.rail.endstops[0][0].mcu_endstop
        self.probe.mcu_probe.set_endstop(self.mapstop)
        self.probe.mcu_probe.query_endstop = self.mapstop.query_endstop
        self.probe.mcu_probe.home_start = self.mapstop.home_start
        self.probe.mcu_probe.home_wait = self.mapstop.home_wait
        self.probe.mcu_probe.get_mcu = self.mapstop.get_mcu
        self.mapstop = oldstop
    
    def _get_startpos(self):
        self.kin_spos = {s.get_name(): round(s.get_commanded_position(),3)
                    for s in self.kin.get_steppers()}
        self.mcu_startpos = {name: s.get_mcu_position()
            for es, name in self.endstops for s in es.get_steppers()}
    
    def _set_endpos(self):
        self.mcu_endpos = {name: s.get_mcu_position()
            for es, name in self.endstops for s in es.get_steppers()}
        zpos = self.kin_spos["stepper_z"] - ((self.mcu_startpos["z"] - self.mcu_endpos["z"]) * self.step_dist["z"])
        self.gcode.run_script_from_command("SET_KINEMATIC_POSITION Z=%.3f\n" % zpos)
        if(self.tp_used):
            opos = self.tp_height
        else:
            opos = 0.
        self.gcode.run_script_from_command("G92 Z%.2f" % opos)

    def cmd_HOME_WZL(self, gcmd):
        self._flip_endstop()
        if self.wzl_cust_homing:
            self._flip_homing_data()
        self._get_startpos()
        self.gcode.run_script_from_command("G28 Z")
        self._flip_endstop()
        self._set_endpos()
        if self.wzl_cust_homing:
            self.rail.change_homing_data(self.orig_homing)
            self.kin.reread_limits()
        self.gcode.run_script_from_command("G1 Z%.2f" % self.wzl_retract)
    
    def cmd_SET_MESHCONFIG(self,gcmd):
        params = gcmd.get_command_parameters()["VALUE"].split(",")
        mesh_config = self.config.getsection("bed_mesh")
        gm = self.printer.lookup_object('gcode_move')
        min = [float(params[0]) + gm.base_position[0],float(params[1]) + gm.base_position[1]]
        max = [float(params[2]) + gm.base_position[0],float(params[3]) + gm.base_position[1]]
        cnt = [int(params[4]),int(params[5])]
        mymesh = self.printer.lookup_object('bed_mesh')
        mymesh.bmc.regenerate_points(min,max,cnt,gm.base_position[2],mesh_config)

    def cmd_CREATE_MESH(self,gcmd):
        gm = self.printer.lookup_object('gcode_move')
        self._flip_endstop()
        self.gcode.run_script_from_command("BED_MESH_CALIBRATE")
        self._flip_endstop()
        self.toolhead.manual_move([None,None,gm.base_position[2] + 10],10)
        self.toolhead.manual_move([gm.base_position[0],gm.base_position[1],None],200)

    def cmd_MOVE_CNC(self,gcmd):
        tpos = self.toolhead.get_position()
        params = gcmd.get_command_parameters()["VALUE"].split(",")
        v = params.pop()
        for i in [0,1,2]:
            tpos[i] += float(params[i])
        self.toolhead.move(tpos,v)
    
    def cmd_ENABLE_TP(self,gcmd):
        self.tp_used = 1
    
    def cmd_DISABLE_TP(self,gcmd):
        self.tp_used = 0
    
    def cmd_PARK_TOOL(self,gcmd):
        self.gcode.run_script_from_command("G1 X%d Y%d\n" % (self.park_x,self.park_y))

    def _handle_mcu_identify(self):
        self.toolhead = self.printer.lookup_object('toolhead')
        self.kin = self.toolhead.get_kinematics()
        self.steppers = self.kin.get_steppers()
        self.endstops = [es for rail in self.kin.rails for es in rail.get_endstops()]
        for rail in self.kin.rails:
            if rail.get_name() == "stepper_z":
                self.rail = rail
                break
        for s in self.steppers:
            if s.get_name()[-1] in "xyz":
                self.step_dist[ s.get_name()[-1]] = s.get_step_dist()
        self.orig_homing = self.rail.get_homing_data()
        self.probe = self.printer.lookup_object('probe')

def load_config(config):
    wzl = Mpcnc(config)
    return wzl
