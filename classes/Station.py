from . import StationStatus
from collections import deque
from random import expovariate
from math import ceil

MAX_CLOCK = 1000000

class Station:
    status = StationStatus.idle
    data_period = 100    #V.A
    data_mean_time = 5   #V.A

    data_queue = deque()
    data_queue_max = 10

    data_events = deque()
    event_memory_window = 20

    data_ttl = 0
    backoff_counter = 0
    backoff_counter_max = 0
    canceled_counter = 0

    time_counter = 0

    def __init__(self):
        pass
    
    ##########################################
    #       GLOBAL STATE HANDLING API        #
    ##########################################

    def send_data(self):
        self.status = StationStatus.data
        return self.data_queue.popleft()
    
    def set_backoff(self, value):
        self.backoff_counter_max = value

    ##########################################
    #          LOCAL STATE HANDLING          #
    ##########################################

    def update_backoff(self):
        self.backoff_counter += 1

    def send_rts(self):
        self.status = StationStatus.rts
    
    # Update data_queue with poisson random variable
    def queue_incoming_event(self):
        event_time = 0
        if len(self.data_queue) == 0:
            event_time = expovariate(1/self.data_period)
        else:
            event_time = expovariate(1/self.data_period) + self.data_events[-1]
        
        self.data_events.append(event_time % MAX_CLOCK)

    def is_data_outgoing(self):
        return ceil(self.data_events[0]) == self.time_counter

    # Manage Station as a finite state machine with random variables
    def next(self):
        # Keep event window length constant
        while (len(self.data_events) < self.event_memory_window):
            self.queue_incoming_event()

        # Checks for outgoing data events
        while (self.is_data_outgoing()):
            self.data_events.popleft()
            self.data_queue.append(
                    ceil(expovariate(1/self.data_mean_time))
                )
            # Drops dataframes that exceed data queue length
            while (len(self.data_queue) > self.data_queue_max):
                self.data_queue.pop()
                self.canceled_counter += 1

        if (self.status == StationStatus.backoff):
            if (self.backoff_counter == self.backoff_counter_max):
                self.send_rts()
            else:
                self.update_backoff()

        self.time_counter = (self.time_counter + 1) % MAX_CLOCK
        return self.status
