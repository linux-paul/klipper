class Estlcam:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = config.get_printer().lookup_object('gcode')

        self.gcode.register_command("M00", self.cmd_M00)
        self.gcode.register_command("M03", self.cmd_M03)
        self.gcode.register_command("M05", self.cmd_M05)
        self.gcode.register_command("G00", self.cmd_G00)
        self.gcode.register_command("G01", self.cmd_G00)
        self.gcode.register_command("G02", self.cmd_G02)
        self.gcode.register_command("G03", self.cmd_G03)

    def cmd_M00(self, gcmd):
        self.gcode.run_script_from_command("M118 Toolchange? resume with RESUME")
        self.gcode.run_script_from_command("PAUSE")
    def cmd_M03(self, gcmd):
        self.gcode.run_script_from_command("M3 %s" % gcmd.get_commandline()[4:])
    def cmd_M05(self, gcmd):
        self.gcode.run_script_from_command("M5 %s" % gcmd.get_commandline()[4:])
    def cmd_G00(self, gcmd):
        self.gcode.run_script_from_command("G0 %s" % gcmd.get_commandline()[4:])
    def cmd_G01(self, gcmd):
        self.gcode.run_script_from_command("G1 %s" % gcmd.get_commandline()[4:])
    def cmd_G02(self, gcmd):
        self.gcode.run_script_from_command("G2 %s" % gcmd.get_commandline()[4:])
    def cmd_G03(self, gcmd):
        self.gcode.run_script_from_command("G3 %s" % gcmd.get_commandline()[4:])


def load_config(config):
    return Estlcam(config)