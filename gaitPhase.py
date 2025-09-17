import numpy as np

class GaitPhase:
    def __init__(self, datarate):
        '''
        This class is to Calculate the gait phase
        @input: datarate, the update rate, unit is Hz.
        '''

        self.last_stance_time = 0.6  # start at 0.6s of stance time, will update each step
        self.MIDSTANCE_ITERS_THRESHOLD = self.last_stance_time * 0.25 * datarate  # 20% of stance time
        self.LATESTANCE_ITERS_THRESHOLD = self.last_stance_time * 0.5 * datarate  # 50% of stance time
        self.SWING_ITERS_THRESHOLD = 5 # for delay filter
        self.SWING_DELAY_ITERS_THRESHOLD_MAX = 14 # 140 ms maximum delay
        self.GYROMAG_THRESHOLD_TOESTRIKE = 45  # unit:degree
        self.GYROMAG_THRESHOLD_HEELOFF = 45  # unit:degree
        self.HEELSTRIKE_ITERS_THRESHOLD = 0.1 * datarate  # 0.1s
        self.DATARATE = datarate

        [self.EARLY_STANCE, self.MID_STANCE, self.LATE_STANCE, self.SWING] = range(4)        
        self.external_gaitphase = 0
        self.gaitphase = self.MID_STANCE
        self.gaitphase_old = self.MID_STANCE
        self.gyroSagittal_old = 0   # used for gait phase detection
        self.step_count = 0
        self.iters_consecutive_below_gyroMag_thresh = 0
        self.iters_stance = 0

        # variables for calculate gait stance ratio
        self.stance_count, self.swing_count, self.stride_count = 0,0,1
        self.swing_delay_flag = 0 # swing phase should be delay.
        self.swing_delay_cont = 0        
        self.empirical_scale = 0.12 # Empirical swing delay cont scale based on experiments.
        self.stanceratio = 1.0
        self.stride_step_number = 0
        self.inactive_period = 3 # default value is 3 seconds
        self.strides_for_average = 7
        self.stanceratio_array=np.ones(int(self.strides_for_average))
        self.average_stanceratio = 1.0
        self.start_walking = False

    def update_gaitphase(self, sensor_data):
        if self.gaitphase == self.SWING:
            self.gaitphase_old = self.SWING
            gyroSagittal = sensor_data['GyroX']
            # self.swing_count > self.SWING_ITERS_THRESHOLD is used as a delay filter
            if (gyroSagittal < 0) and (self.gyroSagittal_old > 0) and (self.swing_count > self.SWING_ITERS_THRESHOLD):   # Negative Gyro zero point indicate Heel Strike event. 
                # self.gaitphase = self.EARLY_STANCE
                self.swing_delay_flag = 1
            if self.swing_delay_flag == 1:
                if self.swing_delay_cont > self.stance_count*self.empirical_scale or self.swing_delay_cont > self.SWING_DELAY_ITERS_THRESHOLD_MAX: # no more than maximum delay.
                    self.gaitphase = self.EARLY_STANCE
                    self.swing_delay_flag = 0
                    self.swing_delay_cont = 0

                self.swing_delay_cont = self.swing_delay_cont + 1

        elif self.gaitphase == self.EARLY_STANCE:
            self.gaitphase_old = self.EARLY_STANCE
            gyroMag = np.linalg.norm(
                [sensor_data['GyroX'], sensor_data['GyroY'], sensor_data['GyroZ']], ord=2)
            if gyroMag < self.GYROMAG_THRESHOLD_TOESTRIKE: # Toe strike threshold
                # If the gyroscope magnitude is below the threshold for a certain time, change to stance phase
                self.iters_consecutive_below_gyroMag_thresh += 1
                if self.iters_consecutive_below_gyroMag_thresh > self.HEELSTRIKE_ITERS_THRESHOLD:
                    self.iters_consecutive_below_gyroMag_thresh = 0
                    self.iters_stance = 0
                    self.step_count += 1
                    self.gaitphase = self.MID_STANCE
            else:
                # If the gyroscope magnitude is larger than the threshold, reset the timer
                self.iters_consecutive_below_gyroMag_thresh = 0
        elif self.gaitphase == self.MID_STANCE:
            self.gaitphase_old = self.MID_STANCE
            self.iters_stance += 1
            if self.iters_stance > self.MIDSTANCE_ITERS_THRESHOLD:
                Gyro_x = sensor_data['GyroX']
                Gyro_y = sensor_data['GyroY']
                Gyro_z = sensor_data['GyroZ']
                gyroMag = np.linalg.norm([Gyro_x, Gyro_y, Gyro_z], ord=2)
                # If the gyroscope magnitude is above the threshold, change to swing phase
                if gyroMag > self.GYROMAG_THRESHOLD_HEELOFF: # Heel off threshold
                    self.last_stance_time = self.iters_stance / self.DATARATE
                    if self.last_stance_time > 2:
                        self.last_stance_time = 2
                    elif self.last_stance_time < 0.4:
                        self.last_stance_time = 0.4
                    self.gaitphase = self.LATE_STANCE

        elif self.gaitphase == self.LATE_STANCE:
            self.gaitphase_old = self.LATE_STANCE
            gyroSagittal = sensor_data['GyroX']
            if (gyroSagittal > 0) and (self.gyroSagittal_old < 0):  # Positive Gyro zero point indicate Heel Strike event. 
                self.gaitphase = self.SWING            

        self.gyroSagittal_old = sensor_data['GyroX']  # store GyroX for next cycle 

        # Update external_gaitphase for output: 0 for stance, 1 for swing
        if self.gaitphase == self.SWING:
            self.external_gaitphase = 1
        else:
            self.external_gaitphase = 0

    def update_stanceratio(self,**kwargs):
        '''
        This function calculates stance ratio of the gait measured by the function: update_gaitphase(self,sensor_data).
        The stance ratio of a step is only updated at the beginning of the next step swing/stance phase. Thus, the stance ratio displayed in current step
        is belonged to the last step (the lasted swing and stance). Where **kwargs allows you to pass key word variable length of arguments to a function. 

        '''
        # update parameters setup after running
        if(self.inactive_period!= kwargs['inactive_period']):
            self.inactive_period = kwargs['inactive_period']

        if(self.strides_for_average!= kwargs['strides_for_average']):
            self.strides_for_average=kwargs['strides_for_average']
            self.stanceratio_array=np.ones(int(self.strides_for_average))

        # count the stance and swing period
        if self.gaitphase==self.SWING:  # start swing phase
            if self.gaitphase_old==self.LATE_STANCE: # indicate just coming into swing, this is defined as a finish of the last step, and the start of the next step
                self.swing_count = 1   # reset the counter
            else: # indicate the gait is still in swing phase
                self.swing_count += 1

        if self.gaitphase!=self.SWING:  # start stance, calculate the ratio at this moment.
            if self.gaitphase_old==self.SWING: # indicate just coming into stance, this is defined as a finish of the last step, and the start of the next step
                self.stride_count = self.stance_count + self.swing_count # sum stride period at the moment of gait switching into stance phase from swing phase
                self.stanceratio = float(self.stance_count)/float(self.stride_count) # calculate stance ratio at the beginning of the stance phase
                # set stance count to one
                self.stance_count = 1
                # ignore the first stride for stance ratio calculation
                if((self.stride_step_number==0) and not self.start_walking): # indicates the current stride is the first stride
                    self.stride_step_number=0
                    self.start_walking=True
                else: # from second strides
                    # count stride step number from the actual second stride
                    self.stride_step_number+=1 # a new stride step

                    # format stance ratio value with two float points
                    self.stanceratio = round(self.stanceratio*100.0)/100.0

                    # calculate average stance ratio
                    self.stanceratio_array[self.stride_step_number % len(self.stanceratio_array)]=self.stanceratio

                    # calculate mean stance ratio of stride_step_number stride
                    if(self.stride_step_number < self.strides_for_average): # consider less than strides_for_average
                        mean_stanceratio = np.mean(self.stanceratio_array[1: self.stride_step_number + 1]) # start from 1, do not include right border.
                    else: # consider stride_step_number stride
                        mean_stanceratio = np.mean(self.stanceratio_array)
                    # format average_stanceratio with two float points
                    self.average_stanceratio = round(mean_stanceratio*100.0)/100.0

            else: # indicate the gait is still in stance phase
                self.stance_count += 1

        if((float(self.swing_count)/self.DATARATE) > self.inactive_period):# if swing phase is timeout, then set the stance ratio equal to 1.0
            self.stanceratio = 1.0
            self.average_stanceratio = 1.0
            self.stride_step_number = 0 # clear the stride step number counter
            self.start_walking = False
            self.swing_count = 0
        if((float(self.stance_count)/self.DATARATE) > self.inactive_period):# if stance phase is timeout, then set the stance ratio equal to 1.0
            self.stanceratio = 1.0
            self.average_stanceratio = 1.0
            self.stride_step_number = 0 # clear the stride step number counter
            self.start_walking = False
            self.stance_count = 1
