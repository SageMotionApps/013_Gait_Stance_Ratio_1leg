# Gait Stance Ratio One Leg
Compute the stance-to-stride ratio for one leg during walking.

## Nodes Required: 1
- **Sensing (1):** foot (top, switch pointing forward)

## Algorithm & Parameters

The app computes the gait phase using raw gyroscope data from a foot-mounted IMU and determines the ratio of stance phase duration to stride duration.

### Parameters
- **Strides for Average**: How many strides are used to compute a running average.
- **Inactive Period (s)**: The maximum allowed duration of no gait phase change before a fallback stance ratio of 1.0 is reported.

## Description of Data in Downloaded File

### Calculated Fields
- **time (sec)**: Time since trial start
- **Gait_Phase**: 0 = Stance, 1 = Swing
- **Stance_Ratio**: Stance-to-stride ratio of a foot

### Sensor Raw Data Values
- `SensorIndex`: index of raw sensor data
- `AccelX/Y/Z (m/s^2)`: raw acceleration data
- `GyroX/Y/Z (deg/s)`: raw gyroscope data
- `MagX/Y/Z (μT)`: raw magnetometer data
- `Quat1/2/3/4`: quaternion data
- `Sampletime`: timestamp
- `Package`: data package number

## App Lifecycle
1. Select app and connect 1 foot sensor
2. Configure parameters
3. Click **Start**
4. Click **Stop** to end trial and download data

## Documentation
For more details, visit the [SageMotion Docs](http://docs.sagemotion.com/index.html)
