import math

STANDARD_DIMENSIONS = [
    'x', 'y', 'z',
    'vx', 'vy', 'vz',
    'velocity',
    'yaw', 'pitch', 'roll'
]

CUSTOM_EQUATIONS = {
    # Example: 'energy': lambda p: p['vx']**2 + p['vy']**2
    'xy_speed': lambda p: math.sqrt(p['vx']**2 + p['vy']**2),
    'vx_magnitude': lambda p: abs(p['vx']),
    'vy_magnitude': lambda p: abs(p['vy']),
    'vz_magnitude': lambda p: abs(p['vz']),
}
