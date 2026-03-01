"""
Scan available cameras and show a live preview of each one.
Press SPACE or N to move to the next camera, Q to quit.
The Kinect 360 RGB typically shows 640x480 with a real image (not a lock icon).
"""
import cv2
import sys


def main():
    print("[detect_cameras] Scanning camera indices 0..7 ...")
    found = []

    for i in range(8):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(i)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            ok, _ = cap.read()
            if ok:
                found.append((i, w, h))
                print("  Index %d: %dx%d  OK" % (i, w, h))
            else:
                print("  Index %d: opened but no frame" % i)
        else:
            print("  Index %d: not available" % i)
        cap.release()

    if not found:
        print("\n[detect_cameras] No cameras found. Check USB connections.")
        return

    print("\n[detect_cameras] Found %d camera(s): %s" % (len(found), [i for i, _, _ in found]))
    print("[detect_cameras] Showing live preview of each camera.")
    print("  SPACE/N = next camera | Q = quit\n")

    for idx, (cam_idx, w, h) in enumerate(found):
        cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(cam_idx)
        if not cap.isOpened():
            continue

        title = "Camera INDEX=%d  (%dx%d)  [%d/%d]  SPACE=next Q=quit" % (
            cam_idx, w, h, idx + 1, len(found)
        )
        print("[detect_cameras] Previewing index %d ..." % cam_idx)

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            cv2.putText(
                frame,
                "INDEX %d  (%dx%d)" % (cam_idx, w, h),
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                "SPACE/N=next  Q=quit",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                1,
            )
            cv2.imshow(title, frame)
            key = cv2.waitKey(30) & 0xFF
            if key == ord("q"):
                cap.release()
                cv2.destroyAllWindows()
                print("\n[detect_cameras] Set CAMERA_INDEX=<chosen index> in projet_kinect/.env")
                return
            if key == ord(" ") or key == ord("n"):
                break

        cap.release()
        cv2.destroyAllWindows()

    print("\n[detect_cameras] All cameras previewed.")
    print("[detect_cameras] Set CAMERA_INDEX=<Kinect index> in projet_kinect/.env")
    print("[detect_cameras] Kinect 360 RGB shows a real image at 640x480.")


if __name__ == "__main__":
    main()
