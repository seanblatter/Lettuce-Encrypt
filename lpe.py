import cv2
import numpy as np
import hashlib
import time

def rtsp_trng(rtsp_url, num_bytes=32):
    """
    Generate a random byte string from an RTSP camera stream.
    
    Args:
        rtsp_url (str): RTSP stream URL (e.g. rtsp://user:pass@192.168.x.x:554/stream1)
        num_bytes (int): How many random bytes to return.
    Returns:
        bytes: Random bytes derived from frame entropy.
    """
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        raise Exception("Cannot open RTSP stream. Check your URL or credentials.")

    entropy_pool = b""

    print("Capturing frames for entropy... (Press Ctrl+C to stop early)")
    start_time = time.time()
    try:
        while len(entropy_pool) < num_bytes * 4:  # gather extra to ensure randomness
            ret, frame = cap.read()
            if not ret:
                continue

            # Convert to grayscale and flatten
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).flatten()

            # Use small sample of random pixels
            pixels = np.random.choice(gray, size=512, replace=False)
            entropy_pool += hashlib.sha256(pixels.tobytes()).digest()

            if time.time() - start_time > 5:
                break  # stop after 5 seconds if not enough entropy

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        cap.release()

    # Final hash for uniform output
    random_bytes = hashlib.sha256(entropy_pool).digest()[:num_bytes]
    return random_bytes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate random bytes from an RTSP or video stream by sampling frame entropy.")
    parser.add_argument("source", nargs="?", default=None,
                        help=("Video source. Provide an RTSP URL (rtsp://...), a video file path, or leave empty to use the default webcam (0)."
                              " If omitted the script will prompt interactively."))
    parser.add_argument("-n", "--num-bytes", type=int, default=32, help="Number of random bytes to generate (default: 32)")
    args = parser.parse_args()

    # Determine source: CLI > interactive prompt > webcam default
    source = args.source
    if source is None:
        try:
            # Provide a clearer prompt and allow blank to mean webcam
            user_input = input("Enter RTSP URL, video file path, or leave blank for webcam (press Enter): ").strip()
        except EOFError:
            user_input = ""

        if user_input == "":
            print("No source provided — using default webcam (index 0).")
            source = 0
        else:
            source = user_input

    # Validate source isn't an empty string (OpenCV requires non-empty filename or an integer index)
    if isinstance(source, str) and source.strip() == "":
        raise SystemExit("Error: empty source provided. Please pass a valid RTSP URL, file path, or leave blank to use webcam.")

    random_bytes = rtsp_trng(source, args.num_bytes)
    random_int = int.from_bytes(random_bytes, "big")

    print(f"\nRandom Bytes: {random_bytes.hex()}")
    print(f"Random Integer: {random_int}")
