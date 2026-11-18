import cv2
import os

def main(camera_index=0, width=1280, height=720):

    # Create the folder to save the calibration photos
    folder_name = "calibration_photos"
    os.makedirs(folder_name, exist_ok=True)

    # Open the camera
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print(f"Could not open the camera (index {camera_index}).")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    window_name = "Calibration Camera - press SPACE to take a photo"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # Number of photos to take
    total_photos = 15
    photo_count = 0

    try:
        while photo_count < total_photos:

            # Read the frame
            ret, frame = cap.read()

            if not ret:
                print("No frame received (the camera may have been disconnected).")
                break

            # Flip horizontally (mirror)
            frame = cv2.flip(frame, 1)

            # Display the frame
            cv2.imshow(window_name, frame)

            # Wait for a key
            key = cv2.waitKey(1) & 0xFF

            # Take a photo with SPACE
            if key == ord(' '):

                photo_count += 1

                # Create the image filename
                filename = f"photo_{photo_count:02d}.jpg"

                # Save the photo
                filepath = os.path.join(folder_name, filename)
                cv2.imwrite(filepath, frame)

                print(f"Photo {photo_count}/{total_photos} saved: {filepath}")

            # Exit with 'q' or ESC
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        pass

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"Calibration photos saved: {photo_count}/{total_photos}")


if __name__ == "__main__":

    main(camera_index=0, width=1280, height=720)