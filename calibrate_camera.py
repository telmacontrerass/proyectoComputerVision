import argparse
import glob
import json
import os
from typing import List

import cv2
import numpy as np


def load_images(filenames: List) -> List:
    return [cv2.imread(filename) for filename in filenames]


def show_image(img: np.array, img_name: str = "Image"):
    cv2.imshow(img_name, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def write_image(output_folder: str, img_name: str, img: np.array):
    os.makedirs(output_folder, exist_ok=True)
    img_path = os.path.join(output_folder, img_name)
    cv2.imwrite(img_path, img)


def list_images(folder: str) -> List[str]:
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG", "*.bmp")
    paths = []
    for ext in extensions:
        paths.extend(glob.glob(os.path.join(folder, ext)))
    return sorted(set(paths))

def detect_corners(imgs: List, paths: List[str], pattern: tuple, show: bool, output_folder: str):
    """Return the refined corners of the images in which the chessboard is detected."""
    subpix_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE

    valid_corners, valid_paths, img_size = [], [], None

    for img, path in zip(imgs, paths):
        name = os.path.basename(path)
        if img is None:
            print(f"  [X] {name}: could not read the image")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if img_size is None:
            img_size = gray.shape[::-1]  
        elif gray.shape[::-1] != img_size:
            print(f"  [X] {name}: size {gray.shape[::-1]} differs from the rest {img_size}, discarded")
            continue

        ok, corners = cv2.findChessboardCorners(gray, pattern, flags)
        if not ok:
            print(f"  [X] {name}: chessboard NOT detected")
            continue

        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), subpix_criteria)
        valid_corners.append(corners)
        valid_paths.append(path)
        print(f"  [OK] {name}: chessboard detected")

        vis = img.copy()
        cv2.drawChessboardCorners(vis, pattern, corners, ok)
        write_image(os.path.join(output_folder, "corners"), f"corners_{name}", vis)
        if show:
            show_image(vis, f"Corners - {name}")

    return valid_corners, valid_paths, img_size


def reprojection_error(objpoints, imgpoints, rvecs, tvecs, K, dist):
    """Per-image and mean reprojection error (RMS, in pixels)."""
    errors = []
    for objp, imgp, rvec, tvec in zip(objpoints, imgpoints, rvecs, tvecs):
        proj, _ = cv2.projectPoints(objp, rvec, tvec, K, dist)
        diff = imgp.reshape(-1, 2) - proj.reshape(-1, 2)
        err = np.sqrt(np.mean(np.sum(diff ** 2, axis=1)))
        errors.append(float(err))
    return errors, float(np.mean(errors))


def calibrate(objpoints, imgpoints, img_size):
    return cv2.calibrateCamera(objpoints, imgpoints, img_size, None, None)


def save_results(output_folder, K, dist, img_size, rms, mean_err, errors, paths):
    os.makedirs(output_folder, exist_ok=True)

    np.savez(os.path.join(output_folder, "calibration.npz"), K=K, dist=dist, img_size=img_size)

    
    data = {
        "image_size_width_height": list(img_size),
        "camera_matrix_K": K.tolist(),
        "distortion_coeffs_k1_k2_p1_p2_k3": dist.ravel().tolist(),
        "fx": float(K[0, 0]),
        "fy": float(K[1, 1]),
        "cx": float(K[0, 2]),
        "cy": float(K[1, 2]),
        "rms_calibrateCamera_px": float(rms),
        "mean_reprojection_error_px": mean_err,
        "error_per_image_px": {os.path.basename(p): e for p, e in zip(paths, errors)},
    }
    with open(os.path.join(output_folder, "calibration.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Camera calibration with a chessboard pattern")
    parser.add_argument("--folder", default="calibration_photos", help="Folder with the chessboard photos")
    parser.add_argument("--cols", type=int, default=9, help="Inner corners along the width")
    parser.add_argument("--rows", type=int, default=6, help="Inner corners along the height")
    parser.add_argument("--square", type=float, default=25.0, help="Side of one square in mm")
    parser.add_argument("--output", default="results_calibration", help="Output folder")
    parser.add_argument("--show", action="store_true", help="Display the images with cv2.imshow")
    args = parser.parse_args()

    pattern = (args.cols, args.rows)

    paths = list_images(args.folder)
    if not paths:
        raise SystemExit(f"No images found in '{args.folder}'. Check the path with --folder.")
    print(f"Images found: {len(paths)}")
    imgs = load_images(paths)

    objp = np.zeros((args.cols * args.rows, 3), np.float32)
    objp[:, :2] = np.mgrid[0:args.cols, 0:args.rows].T.reshape(-1, 2) * args.square

    print(f"\nLooking for a {args.cols}x{args.rows} inner-corner chessboard...")
    imgpoints, valid_paths, img_size = detect_corners(imgs, paths, pattern, args.show, args.output)
    n = len(imgpoints)
    print(f"\nDetected in {n} of {len(paths)} images")
    if n < 3:
        raise SystemExit("At least 3 valid images are needed (ideally 10 or more). "
                         "Check --cols and --rows.")
    if n < 10:
        print("Warning: fewer than 10 valid images, the calibration may be unreliable.")

    objpoints = [objp] * n

    rms, K, dist, rvecs, tvecs = calibrate(objpoints, imgpoints, img_size)
    errors, mean_err = reprojection_error(objpoints, imgpoints, rvecs, tvecs, K, dist)

    np.set_printoptions(precision=4, suppress=True)
    print("\n================ RESULTS ================")
    print(f"Image size (width x height): {img_size}")
    print(f"calibrateCamera RMS: {rms:.4f} px")
    print(f"Mean reprojection error: {mean_err:.4f} px")
    print("\nCamera matrix K:\n", K)
    print(f"\nfx = {K[0, 0]:.2f}  fy = {K[1, 1]:.2f}  cx = {K[0, 2]:.2f}  cy = {K[1, 2]:.2f}")
    print("\nDistortion coefficients (k1, k2, p1, p2, k3):\n", dist.ravel())
    print("\nError per image (px):")
    for p, e in zip(valid_paths, errors):
        flag = "  <-- high, consider removing it" if e > 2 * mean_err and e > 0.5 else ""
        print(f"  {os.path.basename(p)}: {e:.4f}{flag}")

    save_results(args.output, K, dist, img_size, rms, mean_err, errors, valid_paths)
    print(f"\nResults saved in '{args.output}' (calibration.npz, calibration.json, corners/)")


if __name__ == "__main__":
    main()