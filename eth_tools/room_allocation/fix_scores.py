

class GetLocation:
    """Memory efficient location matrix."""
    
    def __init__(self):
        self.locations = ["Schwerzenbach", "Basel", "Lindau Eschikon", 
                  "Zürich Universität", "Zürich Hönggerberg", 
                  "Zürich Oerlikon", "Zürich Zentrum"]
        
        # Values = time in minutes to travel from city1 to city2 by public transport
        distances = [
            [0, 86, 58, 37, 29, 15, 33],
            [86, 0, 90, 82, 84, 69, 67],
            [58, 90, 0, 62, 60, 45, 63],
            [37, 82, 62, 0, 22, 19, 2],
            [29, 84, 60, 22, 0, 21, 24],
            [15, 69, 45, 19, 21, 0, 19],
            [33, 67, 63, 2, 24, 19, 0]
        ]

        self.distances = {(city1, city2): distances[i][j]
                          for i, city1 in enumerate(self.locations)
                          for j, city2 in enumerate(self.locations)}

    def __call__(self, location1, location2):
        return self.distances.get((location1, location2), float('inf'))
    

class GetTypeScore:
    """Memory efficient room type score."""
    
    def __init__(self):
        self.room_types_and_scores = {
            "Seminars / Courses": 100,
            "Meeting room": 100,
            "Exercises": 100,
            "Computer": 70,
            "Lecture hall": 50,
            "Draw": 30,
            "Multipurpose room": 20,
            "Training room": 0,
            "Exhibition space": 0,
            "Photo lab / Darkroom": 0,
            "Laboratory internship": 0,
            "Microscopy": 0,
        }

    def __call__(self, room_type):
        return self.room_types_and_scores.get(room_type, 0)