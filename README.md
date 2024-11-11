# ETH - TOOLS: Room Availability Checker for ETH Zurich

This repository provides a tool to check room availability at ETH Zurich. It not only identifies free rooms but also considers factors like previous schedules to promote a broader distribution of student learning spaces.

## :gear: Setup

We recommend setting up a virtual environment. Using e.g. miniconda, the `room_allocation` package can be installed via:

```bash
conda create -n room-allocation -y python=3.9
conda activate room-allocation

pip install -e .
```

## :person_running: Running from commandline

We provide a helper script for easy usage.
```bash
find-room -l "Zürich Zentrum" --top10
```

This will print the top 10 recommendations for the specified location. Available locations are:
- `"Schwerzenbach"` 
- `"Basel"`
- `"Lindau Eschikon"`
- `"Zürich Universität"`
- `"Zürich Hönggerberg"`
- `"Zürich Oerlikon"`
- `"Zürich Zentrum"`

## :snake: Running from Python

<details>

To run the code, go to the `eth_tools/room_allocation` directory and execute:

```bash
python -m eth_tools.room_allocation.run -l "Zürich Zentrum" --top10
```

### Other Useful Flags

- `-d`, `--duration`: Specify the time duration for which the room should be free.
- `--when`: Specify the date and time when the room should be free. Use the format 'YYYY-MM-DDTHH:MM:SS'
- `-v`, `--verbose`: Enable verbose logging


</details>


## :wrench: Development

<details>
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

</details>

**Authors**: Max Kieffer, Alex Thillen