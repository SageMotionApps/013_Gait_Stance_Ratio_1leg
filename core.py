import time
from sage.base_app import BaseApp
from .gaitPhase import GaitPhase


class Core(BaseApp):
    ###########################################################
    # INITIALIZE APP
    ###########################################################
    def __init__(self, my_sage):
        BaseApp.__init__(self, my_sage, __file__)

        # Constants
        self.DATARATE = self.info["datarate"]

        # Node indices
        self.NODENUM_SENSOR_FOOT_LEFT = self.info["sensors"].index("foot")

        # Initiate GaitPhase subclasses
        self.my_GP_left = GaitPhase(datarate=self.info["datarate"])

        # Initiate variables
        self.iteration = 0

    ###########################################################
    # CHECK NODE CONNECTIONS
    ###########################################################
    def check_status(self):
        sensors_count = self.get_sensors_count()
        err_msg = ""
        if sensors_count < len(self.info["sensors"]):
            err_msg += "Algorithm requires {} sensors but only {} are connected".format(
                len(self.info["sensors"]), sensors_count
            )
        if err_msg != "":
            return False, err_msg
        return True, "Now running Gait Stance Ratio 1 App"

    ###########################################################
    # RUN APP IN LOOP
    ###########################################################
    def run_in_loop(self):
        # GET RAW SENSOR DATA
        data = self.my_sage.get_next_data()
        time_now = self.iteration / self.DATARATE  # time in seconds

        # Compute gait phases
        self.my_GP_left.update_gaitphase(data[self.NODENUM_SENSOR_FOOT_LEFT])

        # Compute gait stance ratio
        self.my_GP_left.update_stanceratio(
            strides_for_average=float(self.config["strides_for_average"]),
            inactive_period=float(self.config["inactive_period"]),
        )

        # CREATE CUSTOM DATA PACKET
        my_data = {
            "time": [time_now],
            "Gait_Phase": [self.my_GP_left.external_gaitphase],
            "Stance_Ratio": [self.my_GP_left.average_stanceratio],
        }

        # SAVE DATA
        self.my_sage.save_data(data, my_data)

        # STREAM DATA
        self.my_sage.send_stream_data(data, my_data)

        # Increment iteration count
        self.iteration += 1
        return True
