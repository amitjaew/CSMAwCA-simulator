from enum import Enum
from random import randint

class AccessPointStatus(Enum):
    idle = 'IDLE'
    data = 'DATA'
    ack = 'ACK'
    rts = 'RTS'
    cts = 'CTS'
    sifs = 'SIFS'
    difs = 'DIFS'

class FrameType(Enum):
    ack = 'ACK'
    rts = 'RTS'
    cts = 'CTS'
    data = 'DATA'

class AccessPoint:
    station_ids = []
    target_station = -1    

    status: AccessPointStatus = AccessPointStatus.idle
    status_queue = []  
    state_counter = 0        #Quantity of time for a determinated state
    state_counter_max = 0    

    T_rts = 1
    T_cts = 1
    T_ack = 1
    T_sifs = 1
    T_difs = 3
    CW_min = 7
    CW_max = 1023
    CW = CW_min

    def __init__(self):
        pass

    def get_backoff(self):
        return randint(1, self.CW)

    def set_state_counter(self, value):    #reset counter
        self.state_counter_max = value
        self.state_counter = 0

    def receive_frame(self, f_type: FrameType, f_len:int):
        if (self.status != AccessPointStatus.idle):
            return False
        if (f_type == FrameType.data):
            # Dataframe Receiving State
            self.status = AccessPointStatus.data
            self.set_state_counter(f_len)

            # Next States
            self.status_queue = [
                AccessPointStatus.difs,
                AccessPointStatus.ack,
                AccessPointStatus.sifs
            ]
        elif (f_type == FrameType.rts):
            # Wait SIFS before senting CTS frame
            self.status = AccessPointStatus.rts
            self.set_state_counter(self.T_rts)
            
            # Send CTS frame and wait SIFS
            self.status_queue = [
                AccessPointStatus.sifs,
                AccessPointStatus.cts,
                AccessPointStatus.sifs,

            ]

    def next(self):
        if (self.status == AccessPointStatus.idle):
            return False

        if (self.state_counter == self.state_counter_max):
            return self.state_handler()

        self.state_counter += 1
        return False

    def state_handler(self):
        output = False

        # Finish sending CTS frame though channel
        if (self.status == AccessPointStatus.cts):
            output = FrameType.cts, self.target_station
        # Finish sending ACK frame though channel
        if (self.status == AccessPointStatus.ack):
            output = FrameType.ack, self.target_station
            self.target_station = -1

        if (len(self.status_queue) > 0):
            self.status = self.status_queue.pop()
            #if (self.status == AccessPointStatus.rts):
            #    self.set_state_counter(self.T_rts)
            if (self.status == AccessPointStatus.cts):
                self.set_state_counter(self.T_cts)
            if (self.status == AccessPointStatus.ack):
                self.set_state_counter(self.T_ack)
            if (self.status == AccessPointStatus.sifs):
                self.set_state_counter(self.T_sifs)
            if (self.status == AccessPointStatus.difs):
                self.set_state_counter(self.T_difs)
        else:
            self.status = AccessPointStatus.idle
            self.set_state_counter(0)

        return output
