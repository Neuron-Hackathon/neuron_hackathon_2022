import pandas as pd
from datetime import timedelta

##### set parameters, do not change! ####

# Test parameters; Do not change!
# e-scooter permit cap: can't have more than 500 scooters in the field
permit = 500

# van capacity
van_capacity = 20

# test period
test_period = []
hour_period = []

for d in range(1, 8):
    for i in range(0, 24):
        test_period.append('2022-07-0{} {}:00:00'.format(d, i))
        hour_period.append(i)
test_period = pd.DataFrame({'datetime':test_period, 'hour_of_day':hour_period})
test_period['datetime'] = pd.to_datetime(test_period['datetime'])
test_period['date'] = test_period['datetime'].apply(lambda x: x.date())

# location of warehouse
wh_x = 6
wh_y = 10

# default values
drive_time = 0.5  # drive 1 unit takes 0.5 min
act_time = 2  # each deploy/retrieve takes 2 min

def model_demand(ttrips):
    """
    a native modelling of scooter demand and supply
    get trip history Dataframe
    return:
        a Dataframe modelling the net needs for scooters
    """

    # Get day of the week to plan for each day
    ttrips['start_day_of_week'] = ttrips.start_time.apply(lambda x: x.day_of_week)
    # Get start hour because output is a shift plan by hour
    ttrips['start_hour_of_day'] = ttrips.start_time.apply(lambda x: x.hour)
    # Extract date from datetime
    ttrips['start_date'] = ttrips.start_time.apply(lambda x: x.date())

    ttrips['end_day_of_week'] = ttrips.end_time.apply(lambda x: x.day_of_week)
    ttrips['end_hour_of_day'] = ttrips.end_time.apply(lambda x: x.hour)
    ttrips['end_date'] = ttrips.end_time.apply(lambda x: x.date())

    demands = ttrips.groupby(['start_date', 'start_hour_of_day', 'start_x', 'start_y']).agg({'trip_id': 'count',
                                                                                             'start_day_of_week': 'min'}).reset_index()
    demands.columns = ['dt', 'hour_of_day', 'x', 'y', 'demand', 'day_of_week']

    supply = ttrips.groupby(['end_date', 'end_hour_of_day', 'end_x', 'end_y']).agg({'trip_id': 'count',
                                                                                    'end_day_of_week': 'min'}).reset_index()
    supply.columns = ['dt', 'hour_of_day', 'x', 'y', 'supply', 'day_of_week']

    # Merge the 2 DF based on a full outer join
    net = demands.merge(supply, how='outer', on=['dt', 'day_of_week', 'hour_of_day', 'x', 'y']).fillna(0)
    net['need'] = net['demand'] - net['supply']

    # get average hourly need for each grid
    hourly_need = net.groupby(['hour_of_day', 'x', 'y']).need.mean().reset_index()
    hourly_need['need'] = hourly_need['need'].round()
    return hourly_need

def get_future_needs(start_hour, end_hour, hourly_need, current_sct_dist):
    """
    get the predicted needs between start_hour and end_hour
    start_hour: int 0-24
    end_hour: int between 0-24
    hourly_need: Dataframe of historical hourly needs, columns: hour_of_day, x, y, need
    current_sct_dist: Dataframe of current scooter counts in all the grids, columns: x, y, sct_cnt

    return future need final_to_add DataFrame
    """
    if start_hour <= end_hour:
        need_snapshot = hourly_need[(hourly_need.hour_of_day >= start_hour) & (hourly_need.hour_of_day < end_hour)]
    # end hour will be less than start hour if its hour 23 --> 23rd hour + 1 = 0 hour    
    else:
        need_snapshot1 = hourly_need[(hourly_need.hour_of_day >= start_hour) & (hourly_need.hour_of_day < 24)]
        need_snapshot2 = hourly_need[(hourly_need.hour_of_day >= 0) & (hourly_need.hour_of_day < end_hour)]
        need_snapshot = pd.concat([need_snapshot1, need_snapshot2], axis=0)

    # sum up all the needs for each grid to see if need to deploy or retrieve
    to_add = need_snapshot.groupby(['x', 'y']).need.sum().reset_index()

    # current_sct_dist is snapshot of where the scooters are located (which grid they are at)
    # to_add shows you what is the demand at each grid
    final_to_add = to_add.merge(current_sct_dist, how='left', on=['x', 'y']).fillna(0)

    final_to_add['need'] = final_to_add['need'] - final_to_add['sct_cnt']

    return final_to_add[['x', 'y', 'need']]


def cap_need(x):
    """
    can't deploy or retrieve more than 20 scooters at one time in a grid
    x: int

    return: capped x
    """
    if x > van_capacity:
        return van_capacity
    elif x < - van_capacity:
        return - van_capacity
    else:
        return x

# Threshold is the min for operator to go to that grid, so if to_add_threshold is 5 then operators will only deploy to grids with 5 or more scooters
def needs_filter(future_need, to_add_threshold=5):
    """
    a function that can be customised to modify the future need
    future_need: Dataframe, columns: 'x', 'y', 'need'
    to_add_threshold: int

    return: filtered future_need Dataframe
    """
    # ignore the grids with deployment needs that are less than the to_add_threshold
    # < 0 means need is negative aka lack of supply
    future_need = future_need[(future_need.need >= to_add_threshold) | (future_need.need < 0)]
    # cap the needs to be under van capacity
    future_need['need'] = future_need['need'].apply(cap_need)
    return future_need


def go_to(van_x, van_y, target_x, target_y):
    """
    get the shortest routes from current van location to the target grid
    van_x, van_y: int, current van location
    target_x, target_y: target grid

    return:
    route Dataframe with columns 'x', 'y' in the order of movement
    van location after movement
    """
    routes = [[van_x, van_y]]
    move_to_x = van_x
    move_to_y = van_y

    # check how many grids to move in x and y direction
    dif_x = target_x - van_x
    dif_y = target_y - van_y
    if dif_x != 0:
        for i in range(abs(dif_x)):
            # > 0 means move right
            if dif_x > 0:
                move_to_x = van_x + i + 1
            else:
                move_to_x = van_x - i - 1
            routes.append([move_to_x, van_y]) # append movement to each grid
    if dif_y != 0:
        for j in range(abs(dif_y)):
            # > 0 means move up
            if dif_y > 0:
                move_to_y = van_y + j + 1
            else:
                move_to_y = van_y - j - 1
            routes.append([move_to_x, move_to_y])

    routes_df = pd.DataFrame(routes)
    routes_df.columns = ['x', 'y']
    return routes_df, move_to_x, move_to_y # move_to_x, move_to_y is the target x, y


def go_back_wh(van_x, van_y):
    return go_to(van_x, van_y, wh_x, wh_y)


def get_distance(x1, y1, x2, y2):
    """
    calculate driving distance between two grids (x1, y1) and (x2, y2)
    """
    return abs((x1 - x2)) + abs((y1 - y2))


def find_nearest_grid(x, y, neighbours):
    """
    x, y: current van location
    neighbours: a list of grids [(x1, y1), (x2, y2)...]
    return: x, y of nearest neighbour, and list of the rest of neighbours
    """
    distance = 99999
    target_x = None
    target_y = None
    neighbour_index = None

    # if no neighbours provided (no list of grids), return None for everything
    if neighbours is None or len(neighbours) == 0:
        return target_x, target_y, neighbour_index

    for i in range(len(neighbours)):
        x1 = neighbours[i][0] # each list has (x, y)
        y1 = neighbours[i][1]
        d = get_distance(x, y, x1, y1) # get distance from current location to grid

        # distance will be replaced if it fulfils criteria and will end up with the minimum distance of grid from current location
        if d >= 0 and d < distance:
            distance = d
            target_x = x1
            target_y = y1
            neighbour_index = i

    neighbours.pop(neighbour_index)
    return target_x, target_y, neighbours


def plan_a_shift(future_need, sdist, shift_id, sct_in_van):
    """
    take predicted future needs ('x', 'y', 'need'), existing scooter distributions,
    shift id and starting scooter number in van
    return:
    1. DataFrame of plan for a shift with: shift id, shift date-time, x, y, flow (add or remove scooters)
    2. Update scooter distribution after shift plan execution
    3. scooters left in van
    """

    # create action list to hold 'x', 'y', 'flow' + for add scooters/ - for remove scooters
    actions = []
    # merge scooter distribution (snapshot of where scooter is), merge with the needs to show the count of scooters in that grid and the need
    sdist1 = sdist.merge(future_need, how='outer', on=['x', 'y']).fillna(0)
    # shows overall value eg if sct count at that grid is 1 means and the need is -2 it means that the grid has too many sct and 1 + (-2) = -1 will be the scooter count after rebalance
    # if if sct_cnt_after_rebalance is >= 0 then leave the value as it is, if less than 0 put 0 because there's no scooters to retrieve
    sdist1['sct_cnt_after_rebalance'] = sdist1['need'] + sdist1['sct_cnt']
    sdist1['sct_cnt_after_rebalance'] = sdist1['sct_cnt_after_rebalance'].apply(lambda x: x if x >= 0 else 0)
    # this will give the actual actions, because it shows the actual amt to deploy or retrieve
    sdist1['actual_need'] = sdist1['sct_cnt_after_rebalance'] - sdist1['sct_cnt']

    # initial van location at shift start
    van_x = 6
    van_y = 10

    # total retrievable, get the total number of scooters that is needed to retrieve aka add up all that has less than 0
    retrievable_sct = sdist1[sdist1.actual_need < 0].actual_need.abs().sum()

    # grids for deploy, check which grid needs deployment of scooters
    to_deploy = sdist1[sdist1.actual_need > 0]
    deploy_nbs = list(zip(to_deploy.x.tolist(), to_deploy.y.tolist()))

    # grids for retrieve, check which grid needs deployment of scooters
    to_retrieve = sdist1[sdist1.actual_need < 0]
    retrieve_nbs = list(zip(to_retrieve.x.tolist(), to_retrieve.y.tolist()))

    # starting from WH, find the nearest to_deploy grid from current van location
    # end while loop when either no more deployment needs or no more retrievable scooters
    actions = []

    while len(deploy_nbs) > 0 and (retrievable_sct + sct_in_van) > 0:
        # return dx, dy --> location of the nearest grid to van and the remaining list of tuples
        dx, dy, deploy_nbs = find_nearest_grid(van_x, van_y, deploy_nbs)
        #  since deploy_nbs > 0 filter out to_deploy df to the target nearest grid and get the number of sct needed
        deploy_need = to_deploy[(to_deploy.x == dx) & (to_deploy.y == dy)]['actual_need'].tolist()[0]

        if sct_in_van >= deploy_need:
            # if there are enough scooters in van to deploy in dx, dy, go to deploy directly and update sct_in_van
            # drive_path is the step by step movement of the van to each grid to reach destination as a df, van_x and van_y will give the latest location of the van
            drive_path, van_x, van_y = go_to(van_x, van_y, dx, dy)
            drive_path['need'] = 0
            drive_path.loc[(drive_path.x == dx) & (drive_path.y == dy), 'need'] = deploy_need
            actions.append(drive_path)

            sct_in_van = sct_in_van - deploy_need

        elif retrievable_sct > 0:
            # if there are not enough scooters in van, check retrivable scooters in the field

            # retrieve in grids until have enough to meet the deploy needs
            retrieved = 0
            while retrieved + sct_in_van < deploy_need:
                rx, ry, retrieve_nbs = find_nearest_grid(van_x, van_y, retrieve_nbs)
                drive_path, van_x, van_y = go_to(van_x, van_y, rx, ry)
                sct_in_grid = to_retrieve[(to_retrieve.x == rx) & (to_retrieve.y == ry)].actual_need.abs().tolist()[0]
                drive_path['need'] = 0
                drive_path.loc[(drive_path.x == rx) & (drive_path.y == ry), 'need'] = -sct_in_grid
                actions.append(drive_path)
                retrieved = retrieved + sct_in_grid

            drive_path, van_x, van_y = go_to(van_x, van_y, dx, dy)
            drive_path['need'] = 0
            drive_path.loc[(drive_path.x == dx) & (drive_path.y == dy), 'need'] = deploy_need
            actions.append(drive_path)

            sct_in_van = sct_in_van + retrieved - deploy_need


        else:
            # if no scooters in van and no retrivable scooters in the field
            break

    drive_path, van_x, van_y = go_back_wh(van_x, van_y)
    drive_path['need'] = 0
    actions.append(drive_path)

    actions_df = pd.concat(actions)
    actions_df['shift_id'] = shift_id
    sdist2 = sdist.merge(actions_df.groupby(['x', 'y']).need.sum().reset_index(), how='outer', on=['x', 'y']).fillna(0)
    sdist2['sct_cnt'] = sdist2['sct_cnt'] + sdist2['need']
    return actions_df, sdist2[['x', 'y', 'sct_cnt']], sct_in_van


def arrange_shift_time(actions_df, shift_date, shift_start):
    # iterate through action rows and assign each shift hour to each row of actions

    # edge case
    if actions_df is None or actions_df.shape[0] == 0:
        return actions_df

    # initialize parameters
    datetime = pd.to_datetime(shift_date).replace(second=0, microsecond=0, minute=0, hour=shift_start)
    prev_x = actions_df.x.tolist()[0]
    prev_y = actions_df.y.tolist()[0]

    # counters
    min_counter = 0

    datetime_list = []
    time_used = []

    actions_df['need'] = actions_df['need'].fillna(0)

    for i, row in actions_df.iterrows():
        t = abs(row.need) * act_time

        if i > 0:
            t = t + get_distance(prev_x, prev_y, row.x, row.y) * drive_time
            prev_x = row.x
            prev_y = row.y

        time_used.append(t)
        min_counter = min_counter + t

        if min_counter <= 60:
            datetime_list.append(datetime)
        else:
            datetime = datetime + timedelta(hours=1)
            datetime_list.append(datetime)

            min_counter = 0  # reset to 0

    actions_df['action_time'] = time_used
    actions_df['datetime'] = datetime_list
    return actions_df[['shift_id', 'datetime', 'x', 'y', 'need', 'action_time']]


def main():
    # load input data

    ttrips = pd.read_csv('../hackathon_training_trip.csv')

    ttrips['start_time'] = pd.to_datetime(ttrips.start_time)
    ttrips['end_time'] = pd.to_datetime(ttrips.end_time)

    tscooters = pd.read_csv('../hackathon_training_scooter.csv')
    tscooters['datetime'] = pd.to_datetime(tscooters.datetime)
    # Groupby by grid lat long and count the number of scooters in that grid
    sct_dist_init = tscooters.groupby(['x', 'y']).scooter_id.count().reset_index()
    # label count of scooters as sct_cnt
    sct_dist_init.columns = ['x', 'y', 'sct_cnt']

    # initial status
    # scooter distribution - which grids are the scooters located at
    sct_dist = tscooters.groupby(['x', 'y']).scooter_id.count().reset_index()
    sct_dist.columns = ['x', 'y', 'sct_cnt']

    # scooter count on the ground -> from sct_dist dataframe get the sct_cnt column and sum it to get scooter count
    sct_cnt = sct_dist.sct_cnt.sum()
    # num scooters in van is the min of van capacity and difference between permit - sct-cnt --> because van capacity is 20 max, permit = 500, if on the ground has 460, means we can deploy 
    # 40 more scooters but van cap is 20 so take 20. If on the ground is 490, means we can only deploy 10 more, hence min(20, 10), van can only take 10 more scooters out
    sct_in_van = min(van_capacity, (permit - sct_cnt))

    # start shift id
    shift_id = 1
    shift_plan = []

    # demand modeling
    predicted_need = model_demand(ttrips)

    # baseline approach: plan and execute shift at hourly basis
    # iterate each row of data in test_period df which is the empty shift planning template created at the start
    for i, row in test_period.iterrows():

        shift_date = row.date
        shift_hour = row.hour_of_day

        # this method finds demands hourly, you can change it accordingly as you wish
        future_need = get_future_needs(shift_hour, shift_hour + 1, predicted_need, sct_dist)
        filtered_future = needs_filter(future_need, to_add_threshold=0)
        plan, sct_dist, sct_in_van = plan_a_shift(filtered_future, sct_dist, shift_id, sct_in_van)
        shift = arrange_shift_time(plan, shift_date, shift_hour)

        if plan.shape[0] > 1:
            shift_plan.append(shift)
            shift_id = shift_id + 1

    shift_plan_df = pd.concat(shift_plan)
    shift_plan_df.to_csv('sample_submission.csv')

if __name__ == '__main__':
    main()
