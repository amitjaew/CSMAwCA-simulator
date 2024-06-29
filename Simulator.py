from classes.AccessPoint import *
from classes.Station import *
from classes import FrameType, StationStatus, AccessPointStatus
from time import sleep, time

class Simulator():
    def __init__(
                self,
                access_point,
                stations
            ):
        station_ids = [idx for idx in range(len(stations))]
        access_point.set_station_ids(station_ids)

        self.access_point = access_point
        self.stations = stations
        self.station_ids = station_ids
        self.reset()

    def iterate(self, verbose=False):
        if (self.access_point.status == AccessPointStatus.backoff):
            self.update_backoff()

        ap_frame = self.access_point.next()

        if(ap_frame):
            ap_frame_type, station_id = ap_frame
            if (ap_frame_type == FrameType.cts):
                frame_length = self.stations[station_id].send_data()
                self.access_point.receive_frame(
                    f_type = FrameType.data,
                    f_len = frame_length,
                    station_id = station_id
                )
            if (ap_frame_type == FrameType.ack):
                self.stations[station_id].receive_ack()
                self.update_backoff()

        if (self.rts_incoming()):
            self.access_point.receive_frame(
                f_type = FrameType.rts,
                station_id = self.backoff_counter
            )
            self.stations[self.backoff_counter].rts_sended()

        toggle_backoff = False
        for station_id in self.station_ids:
            station = self.stations[station_id]
            station.next()

            should_backoff = (
                station.status == StationStatus.waiting and 
                self.access_point.status == AccessPointStatus.idle
            )
            if (should_backoff):
                station.toggle_backoff()
                toggle_backoff = True
            elif (station.status == StationStatus.rts):
                self.access_point.receive_frame(
                    f_type = FrameType.rts,
                    station_id = station_id
                )

        if (toggle_backoff):
            self.access_point.toggle_backoff()
        
        if (verbose):
            print(f'AP status: {self.access_point.status}')
            print(f'AP frame: {ap_frame}')
            print(f'Backoff Counter: {self.backoff_counter} / {len(self.stations) - 1}')
            for station_id in self.station_ids:
                station = self.stations[station_id]
                status = station.get_status()
                data_queue = [k for k in station.data_queue]
                print(f'{"-" * 18}STATION {station_id} {"-" * 18}')
                print(f'status: {status}\tqueue: {data_queue}')
            sleep(1)

    def rts_incoming(self):
        checked_station = self.stations[self.backoff_counter]
        return checked_station.status == StationStatus.backoff

    def update_backoff(self):
        self.backoff_counter = (self.backoff_counter + 1) % len(self.stations)

    def reset(self):
        self.backoff_counter = 0
        self.access_point.reset()
        for station_id in self.station_ids:
            station = self.stations[station_id]
            station.reset()
            station.set_backoff(station_id)

    def simulate(self, N, verbose=False):
        for i in range(N):
            if (verbose):
                print('/' * 50)
                print(f'RUN: {i + 1}')
            self.iterate(verbose=verbose)

    def dump_results(self, verbose=False):
        global_canceled = 0
        global_success = 0
        station_success_rates = []
        for st_id in self.station_ids:
            st = self.stations[st_id]
            global_canceled += st.canceled_counter
            global_success += st.success_counter
            st_success_rate = 0
            if (st.success_counter or st.canceled_counter):
                st_success_rate = st.success_counter / (st.success_counter + st.canceled_counter)
            station_success_rates.append(st_success_rate)
            print(f'station {st_id} accepted: {st.success_counter}')
            print(f'station {st_id} canceled: {st.canceled_counter}')
            print(f'station {st_id} success rate: {100 * st_success_rate}%')

        global_success_rate = global_success / (global_success + global_canceled)
        print(f'global success rate: {100 * global_success_rate}%')
        return [global_success_rate, station_success_rates]


if (__name__ == '__main__'):
    ap = AccessPoint()
    st = [
        Station(),
        Station(),
        Station(),
        Station(),
        Station(),
        Station(),
        Station(),
        Station(),
        Station(),
    ]
    sim = Simulator(ap, st)

    tic = time()
    sim.simulate(
        N=10000000,
        #verbose=True
    )
    toc = time()
    print('elapsed', toc - tic)
    sim.dump_results()
