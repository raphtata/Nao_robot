"""Kinect SDK diagnostic: poll sensor status with retries."""
import ctypes
import time
import sys

ole32 = ctypes.windll.ole32
ole32.CoInitializeEx(None, 0)

k = ctypes.windll.Kinect10

count = ctypes.c_int(0)
k.NuiGetSensorCount(ctypes.byref(count))
print("[diag] Sensors detected: %d" % count.value)
if count.value == 0:
    print("[diag] No Kinect found. Exiting.")
    sys.exit(1)

sensor = ctypes.c_void_p()
hr = k.NuiCreateSensorByIndex(0, ctypes.byref(sensor))
print("[diag] CreateSensor: 0x%08X" % (hr & 0xFFFFFFFF))

vtbl = ctypes.cast(sensor, ctypes.POINTER(ctypes.c_void_p))[0]


def _get_fn(index, restype, *argtypes):
    addr = ctypes.cast(vtbl, ctypes.POINTER(ctypes.c_void_p))[index]
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(addr)


nui_status = _get_fn(18, ctypes.c_int32)
nui_init = _get_fn(3, ctypes.c_int32, ctypes.c_uint32)
nui_shutdown = _get_fn(4, None)

STATUS_NAMES = {
    0x00000000: "S_OK (ready)",
    0x83010001: "E_NUI_DEVICE_NOT_CONNECTED",
    0x83010002: "E_NUI_DEVICE_NOT_READY",
    0x80004005: "E_FAIL",
}

MAX_WAIT = 30
print("[diag] Polling sensor status for up to %d seconds..." % MAX_WAIT)

for i in range(MAX_WAIT):
    st = nui_status(sensor) & 0xFFFFFFFF
    name = STATUS_NAMES.get(st, "unknown")
    print("  [%2ds] NuiStatus = 0x%08X  %s" % (i, st, name))

    if st == 0:
        print("[diag] Sensor is READY. Trying NuiInitialize(COLOR)...")
        hr = nui_init(sensor, 0x00000002) & 0xFFFFFFFF
        print("[diag] NuiInitialize = 0x%08X  %s" % (hr, STATUS_NAMES.get(hr, "")))
        if hr == 0:
            print("[diag] SUCCESS! Kinect SDK initialized.")
            nui_shutdown(sensor)
        break

    time.sleep(1)
else:
    print("[diag] Sensor never became ready after %ds." % MAX_WAIT)
    print("[diag] The 'Kinect for Windows Audio Control' device (PID_02AD) is stuck.")
    print("[diag] Try plugging the Kinect into a DIFFERENT USB port.")
