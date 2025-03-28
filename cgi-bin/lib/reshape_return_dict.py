from enum import Enum

class Method(Enum):
    LATEST = 0
    MODE = 1
    CENTRAL = 2
    ONE_SEC_MODE = 3

def reshape(return_dict, method=Method.LATEST):
    reshaped_dict = {}

    if type(return_dict) is not dict:
        return return_dict

    for k, v in return_dict.items():
        if k == 'frames':
            new_k, new_v = aggregate(v, method)
            # reshaped_dict[new_k] = new_v
            reshaped_dict['judgements'] = {new_k: new_v}

        else:
            reshaped_dict[k] = reshape(v, method=method)

    return reshaped_dict

def reshape_signal(return_dict):
    reshaped_dict = {}

    if type(return_dict) is not dict:
        return return_dict

    for k, v in return_dict.items():
        if k == 'frames':
            new_k, new_v = aggregate_signal(v)
            # reshaped_dict[new_k] = new_v
            reshaped_dict['judgements'] = {new_k: new_v}

        else:
            reshaped_dict[k] = reshape_signal(v)

    return reshaped_dict

def aggregate(return_dict, method):
    if method == Method.LATEST:
        return aggregate_by_latest(return_dict)

    if method == Method.MODE:
        return aggregate_by_mode(return_dict)

    if method == Method.CENTRAL:
        return aggregate_by_central(return_dict)

    if method == Method.ONE_SEC_MODE:
        return aggregate_by_mode_1sec(return_dict)

    return 'frames', return_dict

def aggregate_by_latest(frame_list):
    return_key = ''
    return_value = ''

    target_frame = frame_list[-1]
    for k, v in target_frame.items():
        if k != 'no':
            return_key = k
            return_value = v
            break

    return return_key, return_value

def aggregate_by_mode(frame_list):
    return_key = ''
    return_value = ''

    values_count = {}
    for frame in frame_list:
        for k, v in frame.items():
            if k != 'no':
                return_key = k
                values_count[v] = values_count.get(v, 0) + 1
                break

    return_value = max(values_count, key=values_count.get)

    return return_key, return_value

def aggregate_by_central(frame_list):
    return_key = ''
    return_value = ''

    target_frame = frame_list[int(len(frame_list)/2)]
    for k, v in target_frame.items():
        if k != 'no':
            return_key = k
            return_value = v
            break

    return return_key, return_value

def aggregate_by_mode_1sec(frame_list):
    return_key = ''
    return_value = ''

    if len(frame_list) > 10:
        frame_list = frame_list[0:10]

    values_count = {}
    for frame in frame_list:
        for k, v in frame.items():
            if k != 'no':
                return_key = k
                values_count[v] = values_count.get(v, 0) + 1
                break

    return_value = max(values_count, key=values_count.get)

    return return_key, return_value

def aggregate_signal(frame_list):
    if len(frame_list) < 50:
        return aggregate_signal_by_mode(frame_list)

    target_list = frame_list[-50:]
    frame_with_signal = 0
    for frame in target_list:
        if len(frame['signals']) > 0:
            frame_with_signal += 1

    if frame_with_signal < 50:
        return aggregate_signal_by_mode(target_list)

    return aggregate_signal_by_matrix(target_list)

def aggregate_signal_by_mode(frame_list):
    return_key = 'signal_color_code'
    return_value = 'unknown'

    values_count = {}
    for frame in frame_list:
        for signal in frame['signals']:
            values_count[signal['color']] = values_count.get(signal['color'], 0) + 1

    if len(values_count) > 0:
        return_value = max(values_count, key=values_count.get)

    return return_key, return_value

def aggregate_signal_by_matrix(frame_list):
    return_key = 'signal_color_code'
    return_value = 'unknown'

    colors_list = []
    for i in range(0, 50, 10):
        one_sec_frames = frame_list[i: i+10]
        _, color = aggregate_signal_by_mode(one_sec_frames)
        colors_list.append(color)

    matrix = [
        {'output': 'blue', 'expected_list': ['red', 'red', 'red', 'blue', 'blue']},
        {'output': 'blue', 'expected_list': ['red', 'red', 'blue', 'blue', 'blue']},
        {'output': 'blue', 'expected_list': ['red', 'blue', 'blue', 'blue', 'blue']},
        {'output': 'blue', 'expected_list': ['blue', 'blue', 'blue', 'blue', 'blue']},
        {'output': 'blue_yellow', 'expected_list': ['blue', 'blue', 'blue', 'blue', 'yellow']},
        {'output': 'yellow', 'expected_list': ['blue', 'blue', 'blue', 'yellow', 'yellow']},
        {'output': 'yellow', 'expected_list': ['blue', 'blue', 'yellow', 'yellow', 'yellow']},
        {'output': 'blue_red', 'expected_list': ['blue', 'yellow', 'yellow', 'yellow', 'red']},
        {'output': 'yellow_red', 'expected_list': ['yellow', 'yellow', 'yellow', 'red', 'red']},
        {'output': 'red', 'expected_list': ['yellow', 'yellow', 'red', 'red', 'red']},
        {'output': 'red', 'expected_list': ['yellow', 'red', 'red', 'red', 'red']},
        {'output': 'red', 'expected_list': ['red', 'red', 'red', 'red', 'red']},
    ]

    min_distance = 5
    for row in range(len(matrix)):
        distance = 0
        expected_list = matrix[row]['expected_list']

        for i in range(5):
            if colors_list[i] != expected_list[i]:
                distance += 1

        if distance < min_distance:
            min_distance = distance
            return_value = matrix[row]['output'] if len(matrix[row]['output']) < len(return_value) else return_value

    if min_distance > 1:
        return_value = 'unknown'

    return return_key, return_value
