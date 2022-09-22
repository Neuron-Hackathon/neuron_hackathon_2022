# Problem Motivation

Shared micro-mobility operators provide services to the public by deploying scooters in a permitted area (service area). Users can unlock a scooter via mobile app, ride it and park it anywhere within the permitted area. Without intervention, scooters tend to move from high demand areas to low demand areas, which will be less accessible for the users. As an operator, we attempt to design a data-driven approach to optimize the supply of e-scooter in the service area, by moving scooters from low-demand zones to high-demand zones.

The problem setting is unnecessary identical to the actual operation scheme. We should simplify the problem, so the participants can easily understand the problem and come up with a solution to the problem.



# Timeline

| Timepoint   | Phase                 |
| ----------- | --------------------- |
| 19 Sep 2022 | Registration start    |
| 14 Oct 2022 | Registration deadline |
| 15 Oct 2022 | First phase start     |
| 21 Oct 2022 | First phase deadline  |
| 22 Oct 2022 | Second phase start    |
| 29 Oct 2022 | Second phase deadline |
| 6 Nov 22    | Winner announcement   |







# Problem Definition

## Concepts

| **Term**                | **Description**                                              | **Note**                                                     |
| :---------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| Service area            | A geographical area, where operators are permitted to deploy e-scooters and users are allowed to ride e-scooters. |                                                              |
| Operational grid (grid) | The service area is sliced into grids based on latitudes and longitudes. See figure 1. Each grid is represented by two integers, indicating the index on latitude and longitude respectively. |                                                              |
| Rebalance               | The operation of removing e-scooters from low-demand regions and adding e-scooters to high-demand regions, in order to maximize the available e-scooters for the users. A rebalance can be split into two steps: retrieve and deploy. |                                                              |
| Retrieve                | To remove e-scooters from a grid.                            | Assume retrieving one e-scooter takes 2min                   |
| Deploy                  | To put e-scooters into a grid so that users can use them in the future. | Assume deploying one e-scooter takes 2min                    |
| Rebalancing van (van)   | A large vehicle driven by a person for rebalance work. e-scooters retrieved from a grid can be loaded into the van and driven to other grids for deployment. A van can only go from one grid to its four adjacent grids. For example, a van in grid (2, 3) can only go to grids (1, 3), (3, 3),(2, 2) and (2, 4). | Assume driving from one grid to any of the adjacent grids takes 0.5 min. |
| Ground operator         | The person who drives the van and retrieves/deploys e-scooters. |                                                              |
| Warehouse               | The place inside the service area to store the rebalancing van and the extra e-scooters taken back by the van. | Located in grid (6, 10)                                      |
| Shift                   | A period of time when a ground operator drives a van out from warehouse to rebalance e-scooters and drives back to warehouse with extra e-scooters. All shift must start and end in the warehouse. |                                                              |
| Shift plan              | A plan of actions in chronological order for all the shifts. | A shift should contain a shift_id, date_time, grid x, grid y, needs of e-scooters. See output format session below. |
| Trip                    | A trip is the journey on an e-scooter taken by a user from one grid to another or the same grid. | Trip origin and destination are converted to and provided as grid axises. See input data table and “Trip 2” on figure 1 Below. |
| Organic rebalance       | e-scooters moved from one grid to another or the same grid due to the users' trips. |                                                              |
| Demand satisfaction     | A trip demand is satisfied, if the user is able to locate an available e-scooter in the grid where he/she would like to start the trip. The available e-scooter can be brought to the grid by either rebalance or a previous trip that ends here (a.k.a organic rebalance). |                                                              |
| Revenue                 | The expected payment from the user over the specified trip with an e-scooter. | Provided in input data table in USD                          |
| Cost                    | The expected expense of the rebalance service of all shifts. The operator is paid by shift hours from the start to the end of each shift, regardless of how much work was done during the shift period. | Ground operators are paid by shift hours. Assume unit cost is 30 USD per hourCost per shift = cost per hour * hours from shift start to shift end, regardless of how many minutes actually contribute to the work Total cost will be the sum of all shift costs |

![img](https://github.com/Neuron-Hackathon/neuron_hackathon_2022/blob/main/images/388dd140-aed4-49c2-ac1d-50cce9043efd.png?raw=true)

Figure 1: Slicing Example Service Area in Singapore into Grids (Note: this is NOT the service area for input data)



## Optimisation Objective

The objective of the service scheduling is to maximise the profit by rebalancing the e-scooters, i.e., the difference between the *revenue increase due to rebalance* and *cost of rebalance*.

*Revenue increase due to rebalance* is the difference between trip revenues with submitted shift plan and trip revenues without any shift plan.

*Cost of rebalance* is the total cost of all shifts as described in the concept table.



## Input Data Format

There are two tables in the input data. The first table contains the sample records of the e-scooter trips taken by the riders between T-4 weeks and T  (T = '2022-07-01 00:00:00 UTC'), which represents the e-scooter demands and organic rebalances in different grids at different times. 

*trip_id*: a unique id for each trip

*start_time, end_time*: when a trip starts/ends, in granularity of minutes.

*start_x, start_y*: where a trip starts.

*end_x, end_y*: where a trip ends.

*revenue*: how much the user pays for a trip, in USD.

| **trip_id** | **start_time**      | **end_time**        | **start_x** | **start_y** | **end_x** | **end_y** | **revenue** |
| ----------- | ------------------- | ------------------- | ----------- | ----------- | --------- | --------- | ----------- |
| 9660944     | 2022-06-01 00:04:00 | 2022-06-01 00:06:00 | 7           | 8           | 5         | 10        | 2.35        |
| 9660949     | 2022-06-01 00:05:00 | 2022-06-01 00:10:00 | 12          | 6           | 9         | 7         | 3.7         |
| 9660979     | 2022-06-01 00:15:00 | 2022-06-01 00:20:00 | 5           | 10          | 7         | 10        | 3.25        |
| 9660983     | 2022-06-01 00:17:00 | 2022-06-01 00:20:00 | 5           | 13          | 5         | 10        | 2.8         |
| 9660994     | 2022-06-01 00:20:00 | 2022-06-01 00:29:00 | 3           | 15          | 7         | 9         | 5.05        |

The second table contains the information of e-scooters in different grids at the beginning of T. This will be the starting point for shift planning.

*scooter_id*: a unique id for each e-scooter

*datetime*: when the snapshot of the e-scooter distribution was taken

*x, y*: the grid where an e-scooter located at ‘2022-07-01 00:00:00’

| **e-scooter_id** | **datetime**        | **x** | **y** |
| ---------------- | ------------------- | ----- | ----- |
| 6557             | 2022-07-01 00:00:00 | 4     | 13    |
| 4915             | 2022-07-01 00:00:00 | 6     | 10    |
| 6491             | 2022-07-01 00:00:00 | 5     | 13    |
| 3715             | 2022-07-01 00:00:00 | 5     | 13    |



## Output data format

The output is a shift plan **by hour** in CSV format for T (T = '2022-07-01 00:00:00 UTC') to T+1 week ('2022-07-08 00:00:00 UTC').

A shift plan contains multiple shifts and actions in the shifts in **chronological order**.

Each entry in the table contains:

- *shift_id*:  a unique id for each shift
- *datetime*:  1 hour in the time table, multiple rows can share the same datetime as long as all the driving and deployment/retrieval can be conducted within the time limit.
- *x, y*: the operational grid location (x, y)
- *need*:  the deployment/retrieval to be taken in a grid, which is represented as an integer. If the integer is positive, it indicates the number of e-scooters deployed in the grid. If the integer is negative, it indicates the number of e-scooters retrieved from the grid. If it is 0, no actions are taken and the operator only drives through that grid. 

| **shift_id** | **datetime**        | **x** | **y** | **need** | **Note (optional for submission)** |
| ------------ | ------------------- | ----- | ----- | -------- | ---------------------------------- |
| **1**        | 2022-07-01 00:00:00 | 6     | 10    | 0        | start from warehouse               |
| **1**        | 2022-07-01 00:00:00 | 6     | 9     | -12      | retrieve 12 e-scooters             |
| **1**        | 2022-07-01 00:00:00 | 6     | 8     | 10       | deploy 10 e-scooters               |
| **1**        | 2022-07-01 00:00:00 | 6     | 7     | 0        | drive through                      |
| **1**        | 2022-07-01 00:00:00 | 7     | 7     | 2        | deploy 2 e-scooters                |
| **1**        | 2022-07-01 01:00:00 | 7     | 8     | -15      | retrieve 15 e-scooters             |
| **1**        | 2022-07-01 01:00:00 | 6     | 8     | 0        | drive back                         |
| **1**        | 2022-07-01 01:00:00 | 6     | 9     | 0        | drive back                         |
| **1**        | 2022-07-01 01:00:00 | 6     | 10    | 0        | drive back                         |
| **1**        | 2022-07-01 01:00:00 | 6     | 11    | 0        | drive back                         |
| **1**        | 2022-07-01 01:00:00 | 6     | 10    | 0        | drive back to warehouse            |
| **2**        | 2022-07-01 20:00:00 | 6     | 10    | 0        | start from warehouse               |
| **2**        | 2022-07-01 20:00:00 | 7     | 10    | 0        | drive through                      |
| **2**        | 2022-07-01 20:00:00 | 8     | 10    | 3        | deploy 3 e-scooters                |
| **2**        | 2022-07-01 20:00:00 | 7     | 10    | 0        | drive back                         |
| **2**        | 2022-07-01 20:00:00 | 6     | 10    | 0        | drive back to warehouse            |



## Constraints and Requirements

1. A shift always starts and ends in the warehouse in grid (6, 10). 
2. At any time the total number of e-scooters on the street can’t exceed 500. And the operator can’t deploy or retrieve more than 20 e-scooters at one time in a grid.
3. Each operation staff can move to multiple grids to perform rebalance in 1 hour, but need to be able to finish all the scheduled actions (driving, deploying, retrieving) within each hour.
4. A trip demand is satisfied, if at least one e-scooter is available in the same grid when the user wants to start the trip.
5. Assume only one van is available and each shift can only hire one ground operator.



# Result Validation

Each team submits the CSV of the shift plan to the Hackathon platform. The system rejects the submission if the constraints above are not fully met. The system also returns the error codes indicating any violation of the constraints.

If the submission is fully consistent with the constraints, the system evaluates the shift plan by simulating the operations in the period of the whole week. The profit generated on selected days is returned and revealed during the competition. 

Each team is allowed to submit a new submission only after an hour of their last submission attempt.

The final score will be calculated based on the whole week’s data. The teams are ranked based on the best score of the submissions.



### Validation Assumptions

Three events can happen in a grid: rebalance, demand (user attempting to start a trip), organic rebalance (user ending a trip). 

- All scheduled rebalance actions in a given hour are only effective at the beginning of the **next hour**. 
  - For example,  the ground operator schedules to deploy 5 e-scooters in grid (7, 10), move to  grid (5, 6) and retrieve 3 e-scooters in grid (5, 6) in the hour of 2022-07-08 09:00:00.  e-scooters availability updates in the two grids will be effective at 2022-07-08 10:00:00.
- The impact of ending a trip will be effective **before** any attempt to start a trip.
  - For example, a grid (7, 10) has 2 e-scooters at the beginning of 2022-07-08 10:02:00. During the minute of 2022-07-08 10:02:00,  3 trips ended here and 4 users tried to start trips from here. Since we assume the trip ends happen first, all 4 demands will be considered “satisfied”.