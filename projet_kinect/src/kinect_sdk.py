"""
Minimal ctypes wrapper for Kinect SDK v1.8 (Kinect10.dll).

Provides RGB frame capture from Kinect 360 (first generation).
Only works on Windows with Kinect SDK v1.8 installed.

The Kinect 360 camera is NOT a standard UVC webcam -- it requires the
Kinect SDK runtime to initialise the sensor and stream pixel data.
This module talks directly to Kinect10.dll via COM vtable calls.
"""

import ctypes
import ctypes.wintypes as wt
import sys

import numpy as np

if sys.platform != "win32":
    raise ImportError("kinect_sdk only works on Windows")


# ---- constants -------------------------------------------------------------

S_OK = 0
NUI_INITIALIZE_FLAG_USES_COLOR = 0x00000002
NUI_INITIALIZE_FLAG_USES_DEPTH = 0x00000020
NUI_IMAGE_TYPE_COLOR = 0
NUI_IMAGE_TYPE_DEPTH = 1
NUI_IMAGE_RESOLUTION_640x480 = 2
FRAME_TIMEOUT_MS = 200


# ---- load DLL --------------------------------------------------------------

try:
    _dll = ctypes.windll.Kinect10
except OSError:
    raise ImportError(
        "Kinect10.dll not found. Install Kinect SDK v1.8:\n"
        "https://www.microsoft.com/en-us/download/details.aspx?id=40278"
    )

_dll.NuiGetSensorCount.restype = ctypes.HRESULT
_dll.NuiGetSensorCount.argtypes = [ctypes.POINTER(ctypes.c_int)]

_dll.NuiCreateSensorByIndex.restype = ctypes.HRESULT
_dll.NuiCreateSensorByIndex.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]


# ---- structures -------------------------------------------------------------

class NUI_IMAGE_VIEW_AREA(ctypes.Structure):
    _fields_ = [
        ("eDigitalZoom", ctypes.c_int),
        ("lCenterX", ctypes.c_long),
        ("lCenterY", ctypes.c_long),
    ]


class NUI_IMAGE_FRAME(ctypes.Structure):
    _fields_ = [
        ("liTimeStamp", ctypes.c_int64),
        ("dwFrameNumber", ctypes.c_uint32),
        ("eImageType", ctypes.c_int),
        ("eResolution", ctypes.c_int),
        ("pFrameTexture", ctypes.c_void_p),
        ("dwFrameFlags", ctypes.c_uint32),
        ("ViewArea", NUI_IMAGE_VIEW_AREA),
    ]


class NUI_LOCKED_RECT(ctypes.Structure):
    _fields_ = [
        ("Pitch", ctypes.c_int),
        ("size", ctypes.c_int),
        ("pBits", ctypes.c_void_p),
    ]


# ---- COM vtable helpers -----------------------------------------------------

def _vtbl_addr(obj_ptr, index):
    """Read function-pointer address from a COM object's vtable."""
    vtbl = ctypes.cast(obj_ptr, ctypes.POINTER(ctypes.c_void_p))[0]
    return ctypes.cast(vtbl, ctypes.POINTER(ctypes.c_void_p))[index]


# INuiSensor vtable layout (after IUnknown 0-2):
#  3  NuiInitialize(DWORD dwFlags)
#  4  NuiShutdown()
#  5  NuiSetFrameEndEvent(HANDLE, DWORD)
#  6  NuiImageStreamOpen(int, int, DWORD, DWORD, HANDLE, HANDLE*)
#  7  NuiImageStreamSetImageFrameFlags(HANDLE, DWORD)
#  8  NuiImageStreamGetImageFrameFlags(HANDLE, DWORD*)
#  9  NuiImageStreamGetNextFrame(HANDLE, DWORD, NUI_IMAGE_FRAME*)
# 10  NuiImageStreamReleaseFrame(HANDLE, NUI_IMAGE_FRAME*)

_T_Release = ctypes.WINFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p)

_T_NuiInitialize = ctypes.WINFUNCTYPE(
    ctypes.HRESULT, ctypes.c_void_p, ctypes.c_uint32,
)

_T_NuiShutdown = ctypes.WINFUNCTYPE(None, ctypes.c_void_p)

_T_NuiImageStreamOpen = ctypes.WINFUNCTYPE(
    ctypes.HRESULT,
    ctypes.c_void_p,                        # this
    ctypes.c_int,                           # eImageType
    ctypes.c_int,                           # eResolution
    ctypes.c_uint32,                        # dwImageFrameFlags
    ctypes.c_uint32,                        # dwFrameLimit
    ctypes.c_void_p,                        # hNextFrameEvent
    ctypes.POINTER(ctypes.c_void_p),        # phStreamHandle
)

_T_NuiImageStreamGetNextFrame = ctypes.WINFUNCTYPE(
    ctypes.HRESULT,
    ctypes.c_void_p,                        # this
    ctypes.c_void_p,                        # hStream
    ctypes.c_uint32,                        # dwMillisecondsToWait
    ctypes.POINTER(NUI_IMAGE_FRAME),        # pImageFrame
)

_T_NuiImageStreamReleaseFrame = ctypes.WINFUNCTYPE(
    ctypes.HRESULT,
    ctypes.c_void_p,                        # this
    ctypes.c_void_p,                        # hStream
    ctypes.POINTER(NUI_IMAGE_FRAME),        # pImageFrame
)

# INuiFrameTexture vtable (after IUnknown 0-2):
#  3  BufferLen() -> int
#  4  Pitch() -> int
#  5  LockRect(UINT, NUI_LOCKED_RECT*, RECT*, DWORD)
#  6  GetLevelDesc(UINT, NUI_SURFACE_DESC*)
#  7  UnlockRect(UINT)

_T_LockRect = ctypes.WINFUNCTYPE(
    ctypes.HRESULT,
    ctypes.c_void_p,                        # this
    ctypes.c_uint,                          # Level
    ctypes.POINTER(NUI_LOCKED_RECT),        # pLockedRect
    ctypes.c_void_p,                        # pRect (NULL)
    ctypes.c_uint32,                        # Flags
)

_T_UnlockRect = ctypes.WINFUNCTYPE(
    ctypes.HRESULT,
    ctypes.c_void_p,                        # this
    ctypes.c_uint,                          # Level
)


# ---- KinectSensor class ----------------------------------------------------

class KinectSensor:
    """Capture RGB frames from a Kinect 360 via Kinect SDK v1.8."""

    def __init__(self, sensor_index=0):
        self._sensor = None
        self._stream = None

        # Enumerate sensors
        count = ctypes.c_int(0)
        hr = _dll.NuiGetSensorCount(ctypes.byref(count))
        if hr != S_OK:
            raise RuntimeError("NuiGetSensorCount failed: 0x%08X" % (hr & 0xFFFFFFFF))
        if count.value == 0:
            raise RuntimeError("No Kinect sensor found. Check USB connection.")
        print("[kinect_sdk] Found %d Kinect sensor(s)" % count.value)

        # Create sensor
        sensor = ctypes.c_void_p()
        hr = _dll.NuiCreateSensorByIndex(sensor_index, ctypes.byref(sensor))
        if hr != S_OK:
            raise RuntimeError(
                "NuiCreateSensorByIndex(%d) failed: 0x%08X" % (sensor_index, hr & 0xFFFFFFFF)
            )
        self._sensor = sensor

        # NuiInitialize (vtable 3)
        fn = _T_NuiInitialize(_vtbl_addr(self._sensor, 3))
        hr = fn(self._sensor, NUI_INITIALIZE_FLAG_USES_COLOR)
        if hr != S_OK:
            raise RuntimeError("NuiInitialize failed: 0x%08X" % (hr & 0xFFFFFFFF))

        # NuiImageStreamOpen (vtable 6)
        stream = ctypes.c_void_p()
        fn = _T_NuiImageStreamOpen(_vtbl_addr(self._sensor, 6))
        hr = fn(
            self._sensor,
            NUI_IMAGE_TYPE_COLOR,
            NUI_IMAGE_RESOLUTION_640x480,
            0,      # flags
            2,      # frame limit
            None,   # event handle
            ctypes.byref(stream),
        )
        if hr != S_OK:
            raise RuntimeError("NuiImageStreamOpen failed: 0x%08X" % (hr & 0xFFFFFFFF))
        self._stream = stream

        print("[kinect_sdk] Kinect sensor %d ready (color 640x480)" % sensor_index)

    # ----- public API --------------------------------------------------------

    def get_frame_bgra(self):
        """Return the next colour frame as (480, 640, 4) BGRA numpy array, or None."""
        frame = NUI_IMAGE_FRAME()

        fn = _T_NuiImageStreamGetNextFrame(_vtbl_addr(self._sensor, 9))
        hr = fn(self._sensor, self._stream, FRAME_TIMEOUT_MS, ctypes.byref(frame))
        if hr != S_OK:
            return None

        try:
            texture = frame.pFrameTexture
            locked = NUI_LOCKED_RECT()

            fn = _T_LockRect(_vtbl_addr(texture, 5))
            hr = fn(texture, 0, ctypes.byref(locked), None, 0)
            if hr != S_OK or locked.Pitch == 0 or locked.pBits is None:
                return None

            nbytes = 640 * 480 * 4
            buf = (ctypes.c_uint8 * nbytes).from_address(locked.pBits)
            bgra = np.frombuffer(buf, dtype=np.uint8).reshape(480, 640, 4).copy()

            fn = _T_UnlockRect(_vtbl_addr(texture, 7))
            fn(texture, 0)

            return bgra
        finally:
            fn = _T_NuiImageStreamReleaseFrame(_vtbl_addr(self._sensor, 10))
            fn(self._sensor, self._stream, ctypes.byref(frame))

    def get_frame_rgb(self):
        """Return the next colour frame as (480, 640, 3) RGB numpy array, or None."""
        bgra = self.get_frame_bgra()
        if bgra is None:
            return None
        return bgra[:, :, 2::-1]  # BGRA -> RGB (drop alpha, reverse channels)

    def get_frame_bgr(self):
        """Return the next colour frame as (480, 640, 3) BGR numpy array (OpenCV format), or None."""
        bgra = self.get_frame_bgra()
        if bgra is None:
            return None
        return bgra[:, :, :3]  # BGRA -> BGR (just drop alpha)

    # ----- lifecycle ---------------------------------------------------------

    def close(self):
        if self._sensor:
            try:
                _T_NuiShutdown(_vtbl_addr(self._sensor, 4))(self._sensor)
            except Exception:
                pass
            try:
                _T_Release(_vtbl_addr(self._sensor, 2))(self._sensor)
            except Exception:
                pass
            self._sensor = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()


# ---- quick self-test --------------------------------------------------------

if __name__ == "__main__":
    import cv2

    print("[kinect_sdk] Self-test: capturing 5 seconds of RGB from Kinect 360...")
    with KinectSensor(0) as kinect:
        import time
        t_end = time.time() + 5
        n = 0
        while time.time() < t_end:
            bgr = kinect.get_frame_bgr()
            if bgr is not None:
                n += 1
                cv2.imshow("Kinect 360 RGB (SDK)", bgr)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        cv2.destroyAllWindows()
        print("[kinect_sdk] Captured %d frames in 5s" % n)
