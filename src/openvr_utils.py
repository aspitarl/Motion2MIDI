import numpy as np
import openvr
import math

# Constants
MIDI_CC_MAX = 127
RANGE_SET_BUTTON = 'b'
SEND_DATA_BUTTON = 'a'

class DeviceCollection():
    def __init__(self):
        self.ovr = openvr.init(openvr.VRApplication_Other)
        self.present_devices = []
        self.refresh_present_devices()

    def refresh_present_devices(self):
        poses = self.get_pose()
        self.present_devices = []
        for i in range(openvr.k_unMaxTrackedDeviceCount):
            if poses[i].bDeviceIsConnected:
                device_class = self.ovr.getTrackedDeviceClass(i)
                keep_classes = [openvr.TrackedDeviceClass_Controller, openvr.TrackedDeviceClass_GenericTracker]
                if device_class in keep_classes:
                    self.present_devices.append(Device(self.ovr, i))
        return self.present_devices

    def get_pose(self):
        return self.ovr.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount)

class Device():
    def __init__(self, ovr, index):
        self.ovr = ovr
        self.index = index
        self.range_dict = None
        self.angle_offsets = {'yaw': 0, 'pitch': 0, 'roll': 0}
        self.haptic_loop_counter = 0
        self.enable_half_y = True
        self.enable_haptic = True
        self.invert_toggle = False
        self.roll_y_factor = 1.0
        self.roll_x_factor = 1.0
        self.last_pose_dict = None

    def __repr__(self):
        return "{} (Dev. {}): ".format(self.get_model(), self.index)

    def get_model(self):
        # mod_str = str(self.ovr.getStringTrackedDeviceProperty(self.index, openvr.Prop_ModelNumber_String))
        serial_str = str(self.ovr.getStringTrackedDeviceProperty(self.index, openvr.Prop_SerialNumber_String))

        replace_dict = {
            'LHR-8A2F6CBD': 'Left Controller',
            'LHR-1AB39A86': 'Left Vive',
            'LHR-FB867046': 'Right Controller',
            'LHR-4A9CEADD': 'Right Vive',
        }

        if serial_str in replace_dict:
            mod_str = replace_dict[serial_str]
        else:
            mod_str = str(self.ovr.getStringTrackedDeviceProperty(self.index, openvr.Prop_ModelNumber_String))
            print(f"Serial number {serial_str} for {mod_str} not in replace_dict, using default model name")

        return mod_str

    def get_pose(self):
        pose = self.ovr.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount)
        if pose[self.index].bPoseIsValid:
            return pose[self.index]
        else:
            return None

    def get_controller_state_dict(self):
        result, pControllerState = self.ovr.getControllerState(self.index)
        state_dict = {}
        state_dict['trigger'] = pControllerState.rAxis[1].x
        state_dict['trackpad_touched'] = bool(pControllerState.ulButtonTouched >> 32 & 1)
        state_dict['grip_button'] = bool(pControllerState.ulButtonPressed >> 2 & 1)
        state_dict['ulButtonPressed'] = pControllerState.ulButtonPressed

        # Convert button number system into simpler form
        if state_dict['ulButtonPressed'] in [2, 6]:
            state_dict['button'] = 'b'
        elif state_dict['grip_button']:
            state_dict['button'] = 'a'
        else:
            state_dict['button'] = None

        # Enable sending based on trackpad touch and invert toggle
        state_dict['enable_send'] = state_dict['trackpad_touched'] if not self.invert_toggle else not state_dict['trackpad_touched']

        return state_dict

    def trigger_haptic_pulse(self, duration_micros=1000, axis_id=0):
        self.ovr.triggerHapticPulse(self.index, axis_id, duration_micros)

    def get_pose_dict(self):
        dev_pose = self.get_pose()
        if dev_pose is None:
            return None

        positionarray = convert_to_euler(dev_pose.mDeviceToAbsoluteTracking, roll_x_factor=self.roll_x_factor, roll_y_factor=self.roll_y_factor)
        velocity = dev_pose.vVelocity
        pose_dict = {
            'x': positionarray[0],
            'y': positionarray[1],
            'z': positionarray[2],
            'yaw': positionarray[3],
            'pitch': positionarray[4],
            'roll': positionarray[5],
            'velocity': float(np.linalg.norm([velocity.v[0], velocity.v[1], velocity.v[2]])),
        }

        # Add angle offsets with modulo 360
        for dim in ['yaw', 'pitch', 'roll']:
            pose_dict[dim] = (pose_dict[dim] + self.angle_offsets[dim]) % 360

        return pose_dict

    def update_range_dict(self):
        pose_dict = self.get_pose_dict()
        for dim in pose_dict:
            if pose_dict[dim] < self.range_dict[dim]['min']:
                self.range_dict[dim]['min'] = pose_dict[dim]
            elif pose_dict[dim] > self.range_dict[dim]['max']:
                self.range_dict[dim]['max'] = pose_dict[dim]

    def initialize_range_dict(self):
        self.set_angle_zeros()
        pose_dict = self.get_pose_dict()
        self.range_dict = {dim: {'min': pose_dict[dim], 'max': pose_dict[dim]} for dim in pose_dict}
        self.range_dict['trigger'] = {'min': 0, 'max': 1}

    def set_angle_zeros(self):
        self.angle_offsets = {'yaw': 0, 'pitch': 0, 'roll': 0}
        pose_dict = self.get_pose_dict()
        for dim in ['yaw', 'pitch', 'roll']:
            if pose_dict[dim] > 180:
                self.angle_offsets[dim] = 180 - pose_dict[dim]
            else:
                self.angle_offsets[dim] = 180 + pose_dict[dim]

    def update_range_center(self):
        self.pose_dict = self.get_pose_dict()

        new_cube_center = {dim: (self.range_dict[dim]['max'] + self.range_dict[dim]['min']) / 2 for dim in self.range_dict}

        if self.pose_dict is not None:
            for dim in ['x', 'y', 'z']:
                if not dim in self.range_dict:
                    continue

                last_pose_offset = self.last_pose_dict[dim] - new_cube_center[dim]

                center = self.pose_dict[dim] - last_pose_offset
                size = self.range_dict[dim]['max'] - self.range_dict[dim]['min']
                self.range_dict[dim]['min'] = center - size / 2
                self.range_dict[dim]['max'] = center + size / 2

    def get_scaled_data_dict(self, cc_dict, trigger):
        scaled_data_dict = {}
        pose_dict = self.get_pose_dict()

        for dim in cc_dict:
            if cc_dict[dim]:
                if dim == 'trigger':
                    data_scaled = int(trigger) * MIDI_CC_MAX
                else:
                    half_mode = (dim == 'y') and (trigger == 1) if self.enable_half_y else False
                    data_scaled = self.get_scaled_data_dim(pose_dict, dim, half_mode)

                if dim == 'y' and self.enable_haptic:
                    self.haptic_loop_counter += 1
                    if self.haptic_loop_counter > 10 and data_scaled > 40:
                        scaled_y_vib = int(data_scaled - 40) * 30
                        self.trigger_haptic_pulse(duration_micros=scaled_y_vib)
                        self.haptic_loop_counter = 0

                scaled_data_dict[dim] = data_scaled

        return scaled_data_dict

    def get_scaled_data_dim(self, pose_dict, dim, half_mode):
        length = self.range_dict[dim]['max'] - self.range_dict[dim]['min']
        relative_dist = pose_dict[dim] - self.range_dict[dim]['min']

        if half_mode:
            halflength = length / 2
            if relative_dist > halflength:
                relative_dist = length - relative_dist
            scaled = (relative_dist / halflength) * MIDI_CC_MAX
        else:
            scaled = (relative_dist / length) * MIDI_CC_MAX

        scaled = max(0, min(MIDI_CC_MAX, scaled))
        scaled = curve_quad(scaled, 1)
        return int(scaled)

class NoDevice():
    def __getattr__(self, name):
        def method(*args, **kwargs):
            raise RuntimeError("Tried to call method {} on NoDevice, check device is connected".format(name))
        return method

    def __repr__(self):
        return "No Device Connected"

def curve_quad(cc_val, curve_amt):
    cc_val = cc_val / 127
    cc_out = 127 * (cc_val + curve_amt * (cc_val - cc_val ** 2))
    return cc_out

def convert_to_euler(pose_mat, roll_x_factor=1, roll_y_factor=1):
    t1 = 180 / math.pi * math.atan2(roll_y_factor * pose_mat[1][0], roll_x_factor * pose_mat[0][0])
    t2 = 180 / math.pi * math.atan2(pose_mat[2][0], pose_mat[0][0])
    t3 = 180 / math.pi * math.atan2(pose_mat[2][1], pose_mat[2][2])
    x = pose_mat[0][3]
    y = pose_mat[1][3]
    z = pose_mat[2][3]
    return [x, y, z, t2, t3, t1]

def convert_to_euler_v2(pose_mat):
    t1 = math.atan2(pose_mat[1][2], pose_mat[2][2])
    c2 = math.sqrt(pose_mat[0][0] ** 2 + pose_mat[0][1] ** 2)
    t2 = math.atan2(-pose_mat[0][2], c2)
    s1 = math.sin(t1)
    c1 = math.cos(t1)
    t3 = math.atan2(s1 * pose_mat[2][0] - c1 * pose_mat[1][0], c1 * pose_mat[1][1] - s1 * pose_mat[2][1])
    x = pose_mat[0][3]
    y = pose_mat[1][3]
    z = pose_mat[2][3]
    return [x, y, z, t2 * 180 / math.pi, t1 * 180 / math.pi, t3 * 180 / math.pi]


