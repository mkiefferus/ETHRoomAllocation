# Readme

## Getting started

```bash
python -v # ^3.10
pip install poetry
cd path/to/repo
poetry install
```

## TODO

Initially, get recommendation for room now. next : get recommendation for some date this week.

- [ ] Caching mechanism - use downloaded files if up to date. Else update files by downloading again.
- [ ] Recommendation system for rooms
  - [x] Room needs to be "free" or "Studierendenplätze". `empty_rooms(datetime : datetime) -> bool`
    - [ ] Naive approach - iterate over all rooms and test which room is free.
    - [ ] Hash map approach - build mapping : 
    ```py
    # room_allocations[day][time][allocation_type] -> [room]
    def empty_rooms(datetime : datetime): -> bool
        l1 = room_allocations(datetime.day, datetime.time, "free")
        l2 = room_allocations(datetime.day, datetime.time, "free")
        return l1 + l2
    
    # among these rooms create recommendations + enable filters , e.g. based on how long they are free, where they are located, capacity, ...
    ``` 
- [ ] Create plotly `dash` dashboard or similar
- [ ] additional functionality like Mensa Recommender. "Mensa-Recommender" + "Room-Recommender". 