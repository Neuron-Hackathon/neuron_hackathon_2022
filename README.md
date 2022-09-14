# Problem Motivation

Shared micro-mobility operators provide services to the public by deploying scooters in a permitted area (service area). Users can unlock a scooter via mobile app, ride it and park it anywhere within the permitted area. Without intervention, scooters tend to move from high demand areas to low demand areas, which will be less accessible for the users. As an operator, we attempt to design a data-driven approach to optimize the supply of e-scooter in the service area, by moving scooters from low-demand zones to high-demand zones.

The problem setting is unnecessary identical to the actual operation scheme. We should simplify the problem, so the participants can easily understand the problem and come up with a solution to the problem.



# Problem Definition

## Concepts

| **Term**                | **Description**                                              | **Note**                                                     |
| :---------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| Service area            | A geographical area, where operators are permitted to deploy scooters and users are allowed to ride scooters |                                                              |
| Operational grid (grid) | The service area is sliced into grids based on latitude and longitude. (see figure 1) |                                                              |
| Rebalancing van (van)   | A large vehicle driven by the operator for rebalance work.  A van can only go from one grid to its four adjacent grids. | A van can carry at most 15 scooters. Assume driving from one grid to any of the adjacent grids takes 2min. |
| Shift                   | A period of time when a ground operator drives a van out from warehouse to rebalance scooters and drives back to warehouse with unneeded scooters. |                                                              |
| Rebalance               | The operation of removing scooters from low-demand regions and adding scooters to high-demand regions, in order to maximize the available scooters to the users. A rebalance can be split into two steps: deploy and retrieve. |                                                              |
| Deploy                  | To put scooters into a grid so that users can use them in the future | Assume deploying one scooter takes 3min                      |
| Retrieve                | To remove scooters from a grid and load them to the van      | Assume retrieving one scooter takes 3min                     |
| Shift plan              | A plan of route and rebalance amounts for all shifts.        |                                                              |
| Trip                    | A trip is the journey on scooter from one grid to another grid. | Trip origin and destination are provided in grid axises.     |
| Warehouse               | The place inside the service area to store extra scooters and rebalancing van. All shift must start and end in the warehouse | Located in grid (3, 5)                                       |
| Demand satisfaction     | A trip demand is satisfied, if the user is able to locate an available e-scooter in the grid where he/she would like to start the trip. The available scooter can be brought to the grid by either rebalance or a previous trip that ends here. |                                                              |
| Revenue                 | The expected payment from the user over the specified trip with electric-scooter. |                                                              |
| Cost                    | The expected expense of the rebalance service over a specific region, mainly including the manpower and transportation of the e-scooters. | Ground operators are paid by shift hours. Assume 30 USD per hour. |

![img](https://neuronmobility.atlassian.net/fd9a7453-aab3-451a-8963-6cc12d3eb6b1#media-blob-url=true&id=3f4f7f54-b9df-48fa-9d0a-93662a74ee3e&collection=contentId-1884192769&contextId=1884192769&height=5923&width=10211&alt=)

Figure 1: Slicing Example Service Area in Singapore into Grids (Note: this is NOT the service area for input data)



## Input Data Format

There are two tables in the input data. The first table contains the sample records of the e-scooter trips taken by the riders between T-4 weeks and T+1 week (T = '2022-07-01 00:00:00 UTC'). T-4 week to T is used for training, while T to T+1 week is used for predict shift planning. They contain the information of e-scooter demands in different grids. 

| **trip_id** | **start_time**      | **end_time**        | **start_x** | **start_y** | **end_x** | **end_y** | **Revenue (USD)** |
| :---------- | :------------------ | :------------------ | :---------- | :---------- | :-------- | :-------- | :---------------- |
| 1           | 2022-08-18 07:00:00 | 2022-08-18 07:00:00 | 2           | 1           | 2         | 3         | 4                 |
| 2           | 2022-08-18 08:00:00 | 2022-08-18 09:00:00 | 5           | 1           | 2         | 3         | 8                 |

The second table contains the information of scooters in different grids at the beginning of T. This will be the starting point for shift planning.

| **scooter_id** | **datetime**        | **x** | **y** |
| :------------- | :------------------ | :---- | :---- |
| 123            | 2022-08-18 07:00:00 | 1     | 2     |
| 124            | 2022-08-18 07:00:00 | 2     | 2     |
| 125            | 2022-08-18 15:00:00 | 5     | 1     |



## Output data format

The output is a shift plan by hour in CSV format for T (T = '2022-07-01 00:00:00 UTC') to T+1 week. Each entry in the table corresponds to a shift_id, 1 hour in the time table, the operational grid location (x, y),  the actions to be taken and remaining scooters in the van after the action. If there’s no service scheduled for a given hour, the entry can be skipped. The entries should be in **chronological order**.

| **shift_id** | **operation_time**  | **x** | **y** | **flow (deploy/retrieve scooters from the grid)** | **scooter_in_van** | **Explanation (No need for submission)** |
| :----------- | :------------------ | :---- | :---- | :------------------------------------------------ | :----------------- | :--------------------------------------- |
| 1            | 2022-07-01 00:00:00 | 3     | 5     | 0                                                 | 6                  | start of shift from warehouse            |
| 1            | 2022-07-01 00:00:00 | 3     | 4     | -6                                                | 12                 | retrieve 6 scooters                      |
| 1            | 2022-07-01 00:00:00 | 3     | 3     | 5                                                 | 7                  | deploy 5 scooters                        |
| 1            | 2022-07-01 00:00:00 | 3     | 2     | 0                                                 | 7                  | drive through                            |
| 1            | 2022-07-01 01:00:00 | 2     | 2     | 2                                                 | 5                  | deploy 2 scooters                        |
| 1            | 2022-07-01 01:00:00 | 1     | 2     | -2                                                | 7                  | retrieve 2 scooters                      |
| 1            | 2022-07-01 01:00:00 | 2     | 2     | 0                                                 | 7                  | drive back                               |
| 1            | 2022-07-01 01:00:00 | 3     | 2     | 0                                                 | 7                  | drive back                               |
| 1            | 2022-07-01 01:00:00 | 3     | 3     | 0                                                 | 7                  | drive back                               |
| 1            | 2022-07-01 01:00:00 | 3     | 4     | 0                                                 | 7                  | drive back                               |
| 1            | 2022-07-01 01:00:00 | 3     | 5     | 0                                                 | 7                  | arrive  warehouse, end of shift          |
| 2            | 2022-07-01 20:00:00 | 3     | 5     | 0                                                 | 5                  | start of a new shift from warehouse      |
| 2            | 2022-07-01 20:00:00 | 4     | 5     | 0                                                 | 5                  | drive through                            |
| 2            | 2022-07-01 20:00:00 | 5     | 5     | 3                                                 | 2                  | deploy 3 scooters                        |
| 2            | 2022-07-01 20:00:00 | 4     | 5     | 0                                                 | 2                  | drive back                               |
| 2            | 2022-07-01 20:00:00 | 3     | 5     | 0                                                 | 2                  | end of shift, arrive warehouse           |



## Constraints and Requirements

1.  A shift has a unique shift_id and can be scheduled for at most 8 continuous hours. And there can be at most 3 shifts a day. But it is possible to schedule less shifts for a given day or schedule less hours for a given shift based on predicted demand.
2. A shift always starts and ends in the warehouse in grid (3, 5).
3. Each operation staff can move to multiple grids to perform rebalance in 1 hour, but need to be able to finish all the scheduled actions (driving, deploying, retrieving) within each hour.
4. At any time, the scooters in the van cannot exceed 15. And the operator can’t deploy or retrieve more than 15 scooters at one time.
5. A trip demand is satisfied, if at least one scooter is available in the same grid when the user is expected to start the trip.
6. If the operator worked in an hour, the full hour is counted towards cost, regardless of how many minutes actually contribute to the work. 



## Optimization Objective

The objective of the service scheduling is to maximize the profit by rebalancing the scooters, i.e., the difference between the revenue and cost of rebalance.



# Result Validation

Prepare Python script to calculate the revenue and cost of the rebalance service.



# Data Preparation

Generate a grid zone. And sample the trips in the database and generate the input data.



# Baseline Approach

We will provide the Python codes with the baseline approach to the participants, they can quickly start to try their own algorithm and strategy on our data set.

The baseline algorithm adopts a greedy strategy. We first construct a demand-oriented service schedule, which meets every demand of scooter. In the following iterations, we remove the services on the regions one at a time. In each iteration, we identify the service to remove, which maximizes the (possibly negative) profit of the operations. The iteration continues, until there is no further improvement possible.