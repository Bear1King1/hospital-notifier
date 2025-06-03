class Ambulance:
    def __init__(self, id: str, a_type: str, time_till_arrival: int = 0, desc =""):
        self.id = id
        self.a_type = a_type
        self.desc = desc
        self.time_till_arrival = time_till_arrival

    def update_time(self, t: int):
        self.time_till_arrival = t

    def advance_time(self, by: int):
        self.time_till_arrival = max(0, self.time_till_arrival - by)
